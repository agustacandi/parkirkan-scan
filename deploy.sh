#!/bin/bash

# Script untuk deploy aplikasi Parkirkan Scan ke Google Cloud Run
# 
# Pastikan Anda sudah:
# 1. Install Google Cloud SDK (gcloud)
# 2. Login ke Google Cloud: gcloud auth login
# 3. Set project: gcloud config set project PROJECT_ID
# 4. Configure Docker untuk Artifact Registry: gcloud auth configure-docker asia-southeast2-docker.pkg.dev

set -e  # Exit jika ada error

# Konfigurasi
PROJECT_ID=${1:-"profound-force-461001-c0"}  # Default ke project Anda
SERVICE_NAME="parkirkan-scan"
REGION="asia-southeast2"  # Jakarta region
REPOSITORY="parkirkan-repo"  # Artifact Registry repository name (sesuai dengan yang ada)
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME"

echo "🚀 Memulai deployment ke Cloud Run..."
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Repository: $REPOSITORY"
echo "Image: $IMAGE_NAME"

# Set project
gcloud config set project $PROJECT_ID

# Configure Docker untuk Artifact Registry
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build dan push image ke Artifact Registry
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME

# Deploy ke Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 1 \
    --max-instances 10 \
    --port 8080 \
    --project $PROJECT_ID

echo "✅ Deployment selesai!"

# Get and display service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "Test endpoint dengan:"
echo "curl -X GET $SERVICE_URL/health"
