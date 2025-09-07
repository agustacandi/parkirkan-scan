# Gunakan image dasar yang sudah mendukung PyTorch dan CUDA (untuk GPU)
# Image ini sudah memiliki semua driver dan library yang diperlukan.
FROM pytorch/pytorch:1.13.1-cuda11.6-cudnn8-runtime

# Tentukan direktori kerja di dalam kontainer
WORKDIR /app

# Salin file requirements.txt dan instal dependensi
# Mengapa terpisah? Ini akan mempercepat proses build Docker karena layer pip akan di-cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file proyek Anda ke dalam kontainer
# File .dockerignore yang sudah Anda miliki akan memastikan file tidak penting tidak ikut
COPY . .

# Cloud Run akan menggunakan port 8080 secara default
ENV PORT=8080

# Jalankan server uvicorn saat kontainer dimulai
# Pastikan nama file Python Anda benar (rest_api_v2) dan nama variabel FastAPI (app) juga benar
CMD ["uvicorn", "rest_api_v2:app", "--host", "0.0.0.0", "--port", "8080"]
