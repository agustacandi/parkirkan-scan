#!/usr/bin/env python3
"""
Test script untuk API Parkirkan Scan
Dapat digunakan untuk test local dan deployed API

Usage:
    python test_api.py --url http://localhost:8888  # Local testing
    python test_api.py --url https://your-service-url  # Cloud Run testing
"""

import argparse
import requests
import json
import sys
from pathlib import Path

def test_health_endpoint(base_url):
    """Test health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {result.get('status')}")
            print(f"   Models loaded: {result.get('models_loaded')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_process_image_endpoint(base_url, image_path=None):
    """Test image processing endpoint"""
    print("🖼️  Testing image processing endpoint...")
    
    # Create a simple test image if none provided
    if not image_path:
        print("   No image provided, creating test image...")
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create simple test image with text
            img = Image.new('RGB', (300, 100), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use default font, fallback if not available
            try:
                font = ImageFont.load_default()
            except:
                font = None
                
            draw.text((10, 30), "B1234XYZ", fill='black', font=font)
            
            # Save to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes = img_bytes.getvalue()
            
        except ImportError:
            print("❌ PIL not available and no image provided. Please install Pillow or provide an image path.")
            return False
    else:
        # Read provided image
        try:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
        except Exception as e:
            print(f"❌ Error reading image file: {e}")
            return False
    
    try:
        files = {'file': ('test_image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(
            f"{base_url}/process_image/", 
            files=files, 
            timeout=60  # Longer timeout for AI processing
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Image processing successful")
            print(f"   Status: {result.get('status')}")
            print(f"   Detected text: {result.get('plate_text')}")
            print(f"   Bounding box: {result.get('bounding_box')}")
            print(f"   Confidence: {result.get('confidence')}")
            return True
        else:
            print(f"❌ Image processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Image processing error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test Parkirkan Scan API')
    parser.add_argument('--url', required=True, help='Base URL of the API (e.g., http://localhost:8888 or https://your-service-url)')
    parser.add_argument('--image', help='Path to test image file (optional)')
    parser.add_argument('--skip-image', action='store_true', help='Skip image processing test')
    
    args = parser.parse_args()
    
    base_url = args.url.rstrip('/')
    
    print(f"🚀 Testing API at: {base_url}")
    print("=" * 50)
    
    # Test health endpoint
    health_ok = test_health_endpoint(base_url)
    
    if not health_ok:
        print("\n❌ Health check failed, skipping other tests")
        sys.exit(1)
    
    # Test image processing if not skipped
    if not args.skip_image:
        print()
        image_ok = test_process_image_endpoint(base_url, args.image)
        
        if not image_ok:
            print("\n❌ Image processing test failed")
            sys.exit(1)
    
    print("\n✅ All tests passed!")
    print(f"🎉 API at {base_url} is working correctly")

if __name__ == "__main__":
    main() 