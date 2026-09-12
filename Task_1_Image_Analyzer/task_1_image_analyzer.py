from PIL import Image, ExifTags
from pathlib import Path
import cv2
import pytesseract
import json


def get_file_info(image_path):
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError("Image file does not exist.")

    if not path.is_file():
        raise ValueError("The given path is not a file.")

    try:
        image = Image.open(path)
        image.verify()
        image = Image.open(path)
    except Exception:
        raise ValueError("The file is not a valid image.")

    file_size = path.stat().st_size
    width, height = image.size

    return {
        "file_name": path.name,
        "file_size_bytes": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "image_format": image.format,
        "width": width,
        "height": height
    }


def get_image_properties(image):
    width, height = image.size
    mode = image.mode

    if mode == "RGB":
        channels = 3
    elif mode == "RGBA":
        channels = 4
    elif mode == "L":
        channels = 1
    elif mode == "LA":
        channels = 2
    else:
        channels = "Unknown"

    if width > height:
        orientation = "Landscape"
    elif height > width:
        orientation = "Portrait"
    else:
        orientation = "Square"

    aspect_ratio = round(width / height, 2)

    return {
        "image_mode": mode,
        "channels": channels,
        "orientation": orientation,
        "aspect_ratio": aspect_ratio
    }


def get_exif_data(image):
    exif_data = {}

    try:
        exif = image.getexif()

        for tag_id, value in exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            exif_data[str(tag_name)] = str(value)

    except Exception:
        pass

    return exif_data


def calculate_blur_score(image_path):
    image = cv2.imread(str(image_path))

    if image is None:
        return None

    height, width = image.shape[:2]

    # Ignore borders containing application UI when the image
    # looks like a screenshot.
    if width > 500 and height > 300:
        x1 = int(width * 0.05)
        x2 = int(width * 0.95)
        y1 = int(height * 0.25)
        y2 = int(height * 0.75)

        image = image[y1:y2, x1:x2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur_score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return round(float(blur_score), 2)


def detect_blur(blur_score):
    if blur_score is None:
        return "Unknown"

    # Higher threshold works better for low-detail
    # and visibly blurred images.
    if blur_score < 250:
        return "Blurry"

    return "Clear"


def preprocess_image(image_path, blur_status):
    image = cv2.imread(str(image_path))

    if image is None:
        return None

    height, width = image.shape[:2]

    # For screenshot-like images, focus on the central content.
    if width > 500 and height > 300:
        x1 = int(width * 0.05)
        x2 = int(width * 0.95)
        y1 = int(height * 0.25)
        y2 = int(height * 0.75)

        image = image[y1:y2, x1:x2]

    if width < 1500:
        scale = 1500 / image.shape[1]

        image = cv2.resize(
            image,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    denoised = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0
    )

    sharpened = cv2.addWeighted(
        enhanced,
        2.0,
        denoised,
        -1.0,
        0
    )

    if blur_status == "Blurry":

        processed = cv2.threshold(
            sharpened,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        return processed

    return sharpened


def extract_text(image_path, processed_image=None):

    if processed_image is not None:
        text = pytesseract.image_to_string(
            processed_image,
            config="--psm 11"
        )
    else:
        image = cv2.imread(str(image_path))

        text = pytesseract.image_to_string(
            image,
            config="--psm 11"
        )

    return text.strip()


def get_ocr_confidence(image_path, processed_image=None):

    if processed_image is not None:
        data = pytesseract.image_to_data(
            processed_image,
            config="--psm 11",
            output_type=pytesseract.Output.DICT
        )
    else:
        image = cv2.imread(str(image_path))

        data = pytesseract.image_to_data(
            image,
            config="--psm 11",
            output_type=pytesseract.Output.DICT
        )

    confidence_values = []

    for confidence in data["conf"]:

        try:
            confidence = float(confidence)

            if confidence >= 0:
                confidence_values.append(confidence)

        except ValueError:
            pass

    if not confidence_values:
        return 0

    return round(
        sum(confidence_values) / len(confidence_values),
        2
    )


def classify_image(text, confidence):

    text_length = len(text.strip())

    if text_length >= 20 and confidence >= 30:
        return "Text Image"

    if text_length >= 5 and confidence >= 20:
        return "Mixed Image"

    return "Normal Image"


def generate_description(
    file_info,
    properties,
    blur_status,
    classification
):

    description_parts = []

    description_parts.append(
        f"This is a {properties['orientation'].lower()} "
        f"{file_info['image_format']} image."
    )

    description_parts.append(
        f"The image resolution is "
        f"{file_info['width']} × {file_info['height']} pixels."
    )

    description_parts.append(
        f"It uses {properties['channels']} channel(s) "
        f"and has {properties['image_mode']} color mode."
    )

    description_parts.append(
        f"The image quality assessment is "
        f"{blur_status.lower()}."
    )

    if classification == "Text Image":
        description_parts.append(
            "The image mainly contains detectable text."
        )

    elif classification == "Mixed Image":
        description_parts.append(
            "The image contains both visual content "
            "and detectable text."
        )

    else:
        description_parts.append(
            "No significant amount of text was detected."
        )

    return " ".join(description_parts)


def analyze_image(image_path):

    path = Path(image_path)

    print("\nAnalyzing image...")

    file_info = get_file_info(path)

    image = Image.open(path)

    properties = get_image_properties(image)

    exif_data = get_exif_data(image)

    print("Checking image quality...")

    blur_score = calculate_blur_score(path)

    blur_status = detect_blur(blur_score)

    print("Preprocessing image...")

    processed_image = preprocess_image(
        path,
        blur_status
    )

    print("Running OCR...")

    text = extract_text(
        path,
        processed_image
    )

    confidence = get_ocr_confidence(
        path,
        processed_image
    )

    classification = classify_image(
        text,
        confidence
    )

    description = generate_description(
        file_info,
        properties,
        blur_status,
        classification
    )

    report = {
        "file_information": file_info,

        "image_properties": properties,

        "quality": {
            "blur_score": blur_score,
            "status": blur_status
        },

        "content": {
            "classification": classification,
            "ocr_confidence": confidence,
            "description": description
        },

        "extracted_text": text,

        "metadata": {
            "exif": exif_data
        }
    }

    return report


def save_report(report):

    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    report_path = reports_folder / "image_report.json"

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    return report_path


def print_report(report):

    file_info = report["file_information"]
    properties = report["image_properties"]
    quality = report["quality"]
    content = report["content"]

    print("\n")
    print("=" * 55)
    print("             IMAGE ANALYSIS REPORT")
    print("=" * 55)

    print("\nFILE INFORMATION")
    print("-" * 55)

    print(f"File Name       : {file_info['file_name']}")
    print(f"File Size       : {file_info['file_size_kb']} KB")
    print(f"Format          : {file_info['image_format']}")
    print(
        f"Resolution      : "
        f"{file_info['width']} x {file_info['height']}"
    )

    print("\nIMAGE PROPERTIES")
    print("-" * 55)

    print(f"Mode            : {properties['image_mode']}")
    print(f"Channels        : {properties['channels']}")
    print(f"Orientation     : {properties['orientation']}")
    print(f"Aspect Ratio    : {properties['aspect_ratio']}")

    print("\nIMAGE QUALITY")
    print("-" * 55)

    print(f"Blur Score      : {quality['blur_score']}")
    print(f"Status          : {quality['status']}")

    print("\nCONTENT")
    print("-" * 55)

    print(f"Classification  : {content['classification']}")
    print(f"OCR Confidence : {content['ocr_confidence']}%")

    print("\nDESCRIPTION")
    print("-" * 55)

    print(content["description"])

    print("\nEXTRACTED TEXT")
    print("-" * 55)

    if report["extracted_text"]:
        print(report["extracted_text"])
    else:
        print("No readable text detected.")

    print("\n" + "=" * 55)


def main():

    print("=" * 55)
    print("          MULTIMEDIA ANALYZER - IMAGE")
    print("=" * 55)

    image_path = input(
        "\nEnter image path: "
    ).strip()

    try:

        report = analyze_image(image_path)

        print_report(report)

        report_path = save_report(report)

        print(
            f"\nReport saved to: {report_path}"
        )

    except FileNotFoundError as error:
        print(f"\nError: {error}")

    except ValueError as error:
        print(f"\nError: {error}")

    except Exception as error:
        print(f"\nUnexpected error: {error}")


if __name__ == "__main__":
    main()
