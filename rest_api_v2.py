from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
import numpy as np
import cv2
import io
import os
import torch  # Jika model Anda memerlukannya (TrOCR)
from ultralytics import YOLO  # Sesuaikan dengan cara Anda load YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from contextlib import asynccontextmanager  # Tambahkan import ini

# Variabel global untuk model (dimuat sekali saat startup)
yolo_model = None
trocr_processor = None
trocr_model = None
device = None  # Untuk GPU jika ada


# --- Adaptasi fungsi dari skrip parkirkan-trocr-v2.py ---

def load_yolo_model_server():
    model_path = "v9.pt"  # Pastikan path ini benar di dalam container
    if not os.path.exists(model_path):
        # Di lingkungan server, model harus ada atau berikan error jelas
        raise RuntimeError(f"Model YOLO '{model_path}' tidak ditemukan.")
    try:
        model = YOLO(model_path)
        print("Model YOLO berhasil dimuat.")
        return model
    except Exception as e:
        print(f"Error saat memuat model YOLO: {e}")
        raise RuntimeError(f"Error saat memuat model YOLO: {e}")


def load_ocr_model_server():
    global device
    try:
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
        # Pindahkan model ke GPU jika tersedia di server dan diinginkan
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        print(f"TrOCR model loaded on: {device}")
        print("Model TrOCR berhasil dimuat.")
        return processor, model
    except Exception as e:
        print(f"Error saat memuat model TrOCR: {e}")
        raise RuntimeError(f"Error saat memuat model TrOCR: {e}")


def detect_license_plate_server(frame, current_yolo_model):  #
    results = current_yolo_model(frame)
    if len(results) > 0:
        result = results[0]
        if len(result.boxes) > 0:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            if len(boxes) > 0:
                best_idx = np.argmax(confs)
                best_box = boxes[best_idx]
                # Pastikan best_box memiliki 4 elemen sebelum unpacking
                if len(best_box) == 4:
                    x1, y1, x2, y2 = best_box
                    x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(frame.shape[1], int(x2)), min(frame.shape[0],
                                                                                                         int(y2))
                    if x2 > x1 and y2 > y1:
                        cropped_img = frame[y1:y2, x1:x2]
                        return True, cropped_img, [x1, y1, x2, y2], float(confs[best_idx])
    return False, None, None, 0.0


def convert_to_grayscale_server(image):  #
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def read_text_trocr_server(image, current_processor, current_model):  #
    global device  # Pastikan device diakses dengan benar
    if len(image.shape) == 2:  # Jika sudah grayscale
        pil_image = Image.fromarray(image).convert('RGB')  # TrOCR biasanya butuh 3 channel
    else:  # Jika masih BGR
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    pixel_values = current_processor(pil_image, return_tensors="pt").pixel_values
    if device:  # Pindahkan tensor ke device yang sama dengan model
        pixel_values = pixel_values.to(device)

    generated_ids = current_model.generate(pixel_values)
    generated_text = current_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return generated_text


# --- Akhir adaptasi fungsi ---


# Definisikan lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Kode yang dijalankan sebelum aplikasi mulai menerima request (startup)
    global yolo_model, trocr_processor, trocr_model
    print("Memuat model saat startup...")
    try:
        yolo_model = load_yolo_model_server()
        trocr_processor, trocr_model = load_ocr_model_server()
        print("Semua model berhasil dimuat. Server siap.")
    except RuntimeError as e:
        # Jika model gagal dimuat, server mungkin tidak berguna.
        print(f"KRITIS: Gagal memuat model saat startup: {e}")
        # Untuk Cloud Run, jika startup gagal, instance mungkin tidak sehat.
        # Pertimbangkan untuk raise error di sini jika model adalah krusial
        # raise # Ini akan menghentikan aplikasi jika model gagal dimuat

    yield  # Aplikasi berjalan di sini

    # Kode yang dijalankan setelah aplikasi selesai menerima request (shutdown)
    # Misalnya, membersihkan resource jika ada
    print("Menjalankan event shutdown (jika ada pembersihan)...")
    # Contoh:
    # if yolo_model: del yolo_model
    # if trocr_model: del trocr_model
    # if trocr_processor: del trocr_processor
    # print("Model telah di-unload.")


# Inisialisasi FastAPI dengan lifespan manager
app = FastAPI(title="API Deteksi Plat Nomor", lifespan=lifespan)


@app.post("/process_image/")
async def process_image(file: UploadFile = File(...)):
    if not yolo_model or not trocr_processor or not trocr_model:
        # Ini terjadi jika model gagal dimuat saat startup
        raise HTTPException(status_code=503, detail="Model belum siap, coba lagi nanti.")
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv2 is None:
            raise HTTPException(status_code=400, detail="File gambar tidak valid.")

        # Deteksi plat nomor
        detected, cropped_img, bbox, conf = detect_license_plate_server(img_cv2, yolo_model)

        if detected and cropped_img is not None:
            # Konversi ke grayscale dilakukan SEBELUM dikirim ke TrOCR jika diperlukan oleh model TrOCR Anda
            # Namun, read_text_trocr_server saya sudah menangani konversi internal ke RGB jika inputnya grayscale
            # jadi convert_to_grayscale_server(cropped_img) mungkin tidak perlu dipanggil di sini jika
            # read_text_trocr_server sudah cukup.
            # Untuk konsistensi dengan kode lama, saya biarkan:
            plate_text = read_text_trocr_server(cropped_img, trocr_processor, trocr_model)
            return {
                "status": "success",
                "plate_text": plate_text,
                "bounding_box": bbox,  # Format: [x1, y1, x2, y2]
                "confidence": conf
            }
        else:
            return {
                "status": "not_detected",
                "plate_text": None,
                "bounding_box": None,
                "confidence": 0.0
            }
    except Exception as e:
        print(f"Error saat memproses gambar: {e}")
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {str(e)}")


@app.get("/health")
async def health_check():
    # Endpoint sederhana untuk memeriksa apakah server berjalan
    models_are_loaded = yolo_model is not None and trocr_model is not None and trocr_processor is not None
    return {"status": "healthy" if models_are_loaded else "degraded", "models_loaded": models_are_loaded}


# Untuk testing lokal:
if __name__ == "__main__":
    import uvicorn
    import os

    # Cloud Run akan menyediakan PORT environment variable
    # Untuk testing lokal, gunakan port 8888 sebagai default
    port = int(os.environ.get("PORT", 8888))
    uvicorn.run(app, host="0.0.0.0", port=port)