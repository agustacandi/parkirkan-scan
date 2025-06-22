# Use Python 3.11 slim as base image for better performance
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgoogle-perftools4 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and model
COPY rest_api_v2.py .
COPY v9.pt .

# Create non-root user for security (Cloud Run best practice)
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port (Cloud Run will inject PORT environment variable)
EXPOSE 8080

# Command to run the application
# Use $PORT environment variable that Cloud Run provides
CMD exec uvicorn rest_api_v2:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 