#!/bin/bash

# Script untuk deploy aplikasi Parkirkan Scan ke Google Cloud Run TANPA Docker lokal
# Menggunakan Cloud Build untuk build image di cloud

set -e  # Exit jika ada error

# Konfigurasi
PROJECT_ID=${1:-"profound-force-461001-c0"}
SERVICE_NAME="parkirkan-scan"
REGION="asia-southeast2"

echo "🚀 Memulai deployment ke Cloud Run (tanpa Docker lokal)..."
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Method: Cloud Build"

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs yang diperlukan
echo "📋 Enabling required APIs..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# Deploy menggunakan Cloud Build
echo "☁️  Building and deploying with Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

echo "✅ Deployment selesai!"

# Get service URL
SERVICE_URL=$(gcloud run services describe parkirkan-scan --region=asia-southeast2 --format='value(status.url)')
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "Test dengan:"
echo "curl -X GET $SERVICE_URL/health"
