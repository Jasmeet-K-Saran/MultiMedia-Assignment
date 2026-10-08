import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import io

st.set_page_config(page_title="Task 5: Image Enhancer", layout="wide")

st.title("Task 5: Image Enhancement & Filtering")
st.write("Upload an image to apply contrast adjustments, sharpening, denoising, and custom filters.")

# Sidebar settings
st.sidebar.header("Enhancement Controls")
uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # Load original image
    image = Image.open(uploaded_file).convert("RGB")
    
    # Sidebar Sliders for Adjustments
    brightness_factor = st.sidebar.slider("Brightness", min_value=0.2, max_value=2.5, value=1.0, step=0.1)
    contrast_factor = st.sidebar.slider("Contrast", min_value=0.2, max_value=2.5, value=1.0, step=0.1)
    sharpness_factor = st.sidebar.slider("Sharpness", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
    color_factor = st.sidebar.slider("Color Saturation", min_value=0.0, max_value=2.5, value=1.0, step=0.1)
    
    # Advanced Processing Options
    st.sidebar.markdown("---")
    st.sidebar.subheader("Advanced Processing")
    apply_clahe = st.sidebar.checkbox("Auto Contrast (CLAHE)")
    apply_denoise = st.sidebar.checkbox("Denoise Filter")
    custom_filter = st.sidebar.selectbox(
        "Apply Artistic Filter",
        ["None", "Edge Enhancement", "Emboss", "Smooth/Blur", "Pencil Sketch", "Grayscale"]
    )

    # 1. Basic Adjustments (PIL)
    enhanced_img = ImageEnhance.Brightness(image).enhance(brightness_factor)
    enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(contrast_factor)
    enhanced_img = ImageEnhance.Color(enhanced_img).enhance(color_factor)
    enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(sharpness_factor)

    # 2. Convert to OpenCV format (NumPy array) for computer-vision filters
    img_cv = np.array(enhanced_img)
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    if apply_clahe:
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        img_cv = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Denoising
    if apply_denoise:
        img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)

    # Back to PIL for display/export
    final_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    # Apply Artistic / Preset Filters
    if custom_filter == "Edge Enhancement":
        final_img = final_img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    elif custom_filter == "Emboss":
        final_img = final_img.filter(ImageFilter.EMBOSS)
    elif custom_filter == "Smooth/Blur":
        final_img = final_img.filter(ImageFilter.SMOOTH_MORE)
    elif custom_filter == "Grayscale":
        final_img = final_img.convert("L")
    elif custom_filter == "Pencil Sketch":
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256.0)
        final_img = Image.fromarray(sketch)

    # Display Side-by-Side Comparison
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Image")
        st.image(image, use_container_width=True)
        st.caption(f"Dimensions: {image.width}x{image.height}px")

    with col2:
        st.subheader("Enhanced Image")
        st.image(final_img, use_container_width=True)
        
        # Download button
        buf = io.BytesIO()
        final_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="Download Enhanced Image",
            data=byte_im,
            file_name="enhanced_image.png",
            mime="image/png"
        )
else:
    st.info("Upload an image in the sidebar to start enhancing.")
