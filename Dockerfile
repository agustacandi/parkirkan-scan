# Dockerfile
FROM python:3.11-slim

# 1) System libs untuk OpenCV & multimedia
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 ffmpeg ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -U pip && pip install -r requirements.txt

# salin source
COPY . .

# 2) Pastikan listen ke 0.0.0.0 dan pakai PORT dari env Cloud Run
ENV PORT=8080
# Opsional: hindari oversubscription CPU
ENV OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 NUMEXPR_NUM_THREADS=2 TORCH_NUM_THREADS=2

# 3) Jalankan uvicorn langsung (ubah modul kalau bukan rest_api_v2:app)
CMD ["sh","-c","exec uvicorn rest_api_v2:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
