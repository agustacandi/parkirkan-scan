# 🚀 Deployment Guide - Parkirkan Scan API ke Google Cloud Run

## 📋 Prerequisites

1. **Google Cloud Account** dengan billing enabled
2. **Google Cloud SDK** terinstall dan configured
3. **Docker** terinstall di local machine
4. **Project Google Cloud** sudah dibuat

## 🛠️ Setup Awal

### 1. Install Google Cloud SDK
```bash
# Untuk macOS
brew install --cask google-cloud-sdk

# Untuk Ubuntu/Debian
curl https://sdk.cloud.google.com | bash
```

### 2. Login dan Setup Project
```bash
# Login ke Google Cloud
gcloud auth login

# Set project ID (ganti dengan project ID Anda)
gcloud config set project YOUR_PROJECT_ID

# Enable APIs yang diperlukan
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Configure Docker untuk Google Cloud
```bash
gcloud auth configure-docker
```

## 🚀 Cara Deploy

### Opsi 1: Manual Deploy (Recommended untuk pertama kali)

1. **Edit PROJECT_ID di script deployment:**
   ```bash
   # Edit file deploy.sh, ganti YOUR_PROJECT_ID
   nano deploy.sh
   ```

2. **Jalankan deployment:**
   ```bash
   ./deploy.sh YOUR_PROJECT_ID
   ```

### Opsi 2: Menggunakan Cloud Build (Automated)

1. **Setup trigger di Google Cloud Console:**
   - Buka Cloud Build > Triggers
   - Connect repository (GitHub/Cloud Source)
   - Buat trigger dengan config file `cloudbuild.yaml`

2. **Atau deploy via command line:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml .
   ```

## ⚙️ Konfigurasi Penting

### Resource Allocation
Aplikasi ini menggunakan AI models yang membutuhkan:
- **Memory**: 4GB (minimum untuk TrOCR + YOLO)
- **CPU**: 2 cores
- **Timeout**: 5 menit per request
- **Concurrency**: 1 (satu request per instance)

### Environment Variables
Cloud Run akan otomatis menyediakan:
- `PORT`: Port yang harus digunakan aplikasi (default: 8080)

## 🧪 Testing

### Health Check
```bash
curl -X GET https://YOUR_SERVICE_URL/health
```

### Test Image Processing
```bash
curl -X POST https://YOUR_SERVICE_URL/process_image/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/image.jpg"
```

## 💰 Estimasi Cost

**Perkiraan biaya bulanan (usage moderate):**
- Instance dengan 4GB RAM, 2 CPU: ~$50-100/bulan
- Cold start time: 30-60 detik (karena AI models)
- Request processing: 2-10 detik per image

**Tips menghemat cost:**
- Set `--max-instances` sesuai kebutuhan
- Gunakan `--concurrency` 1 untuk menghindari OOM
- Monitor usage di Google Cloud Console

## 🔧 Troubleshooting

### 1. Out of Memory Error
- Increase memory allocation to 8GB jika diperlukan
- Check model loading di startup logs

### 2. Cold Start Terlalu Lama
- Consider menggunakan Cloud Run dengan minimum instances
- Atau implement model caching strategy

### 3. Model tidak ditemukan
- Pastikan file `v9.pt` ada di directory yang sama
- Check Dockerfile COPY instruction

### 4. Permission Error
```bash
# Fix Docker permission
sudo usermod -aG docker $USER
# Logout dan login kembali
```

## 📊 Monitoring

Monitor aplikasi di:
1. **Google Cloud Console** > Cloud Run > parkirkan-scan
2. **Logs**: Lihat startup dan request logs
3. **Metrics**: CPU, Memory, Request latency
4. **Error Reporting**: Automatic error tracking

## 🔒 Security Notes

⚠️ **PENTING**: Aplikasi saat ini deployed dengan `--allow-unauthenticated`

Untuk production, pertimbangkan:
1. Remove `--allow-unauthenticated` flag
2. Implement API key authentication  
3. Use Cloud IAM untuk access control
4. Setup VPC connector jika perlu

## 📁 File Structure setelah Setup

```
parkirkan-scan/
├── Dockerfile              # Container configuration
├── .dockerignore           # Files to exclude from build
├── requirements.txt        # Python dependencies
├── rest_api_v2.py         # Main application
├── v9.pt                  # YOLO model file
├── cloudbuild.yaml        # Cloud Build configuration
├── deploy.sh              # Manual deployment script
└── README_DEPLOYMENT.md   # This file
```

## 🆘 Support

Jika mengalami issues:
1. Check logs: `gcloud run logs tail parkirkan-scan --region=asia-southeast2`
2. Verify billing account active
3. Check resource quotas di Google Cloud Console 