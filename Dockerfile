# 1. Gunakan base image yang ringan
FROM python:3.11-slim

# 2. Set environment variables untuk port dan logging
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# 3. Tentukan direktori kerja di dalam kontainer
WORKDIR /app

# 4. Install dependensi sistem yang dibutuhkan oleh OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 5. Salin file requirements yang sudah dioptimalkan
# Ini menggunakan requirements.optimized.txt untuk build yang lebih cepat
COPY requirements.optimized.txt ./requirements.txt

# 6. Install dependensi Python secara efisien
# - Upgrade pip
# - Install torch versi CPU-only terlebih dahulu
# - Install sisa package dari requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 7. Salin semua kode aplikasi dan file model
COPY . .

# 8. (PENTING) Pastikan file model disalin dengan benar
# Baris ini untuk memastikan, meskipun Anda sudah punya
COPY v9.pt .

# 9. Expose port yang akan digunakan
EXPOSE 8080

# 10. (PERBAIKAN UTAMA) Perintah untuk menjalankan aplikasi
# - Menggunakan Gunicorn sebagai production server
# - Menggunakan `--bind 0.0.0.0:$PORT` agar port bersifat dinamis sesuai perintah Cloud Run
# - Menggunakan worker class dari Uvicorn yang cocok untuk FastAPI
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "300", "--bind", "0.0.0.0:$PORT", "rest_api_v2:app", "-k", "uvicorn.workers.UvicornWorker"]