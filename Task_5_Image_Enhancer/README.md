# Task 5: Image Enhancement & Filtering

An interactive Streamlit application for digital image processing and enhancement.

## Features
- **Basic Adjustments**: Brightness, Contrast, Sharpness, and Color Saturation.
- **Advanced Processing**: 
  - CLAHE (Contrast Limited Adaptive Histogram Equalization) via OpenCV LAB color space.
  - Fast Non-Local Means Denoising.
- **Artistic Filters**: Edge Enhancement, Emboss, Smoothing, Grayscale, and Pencil Sketch.
- **Export**: Real-time side-by-side comparison and processed image download.

## How to Run
```bash
pip install -r requirements.txt
streamlit run app.py
