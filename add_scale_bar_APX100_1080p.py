from PIL import ImageFont, ImageDraw, Image
import cv2
import numpy as np
import argparse
import os
import sys
import re
import glob

# OLYMPUS APX100 scopes
DISPLAY_SCALE_NUMBER = True

# Constants from the calibration of the scopes
scale_pixel_4X_100_um = 55
scale_pixel_10X_100_um = 135
scale_pixel_40X_100_um = 555

scale_bar_location_x_offset = 35
scale_bar_location_y_offset = 45
scale_bar_font_size = 30
text_position_y_offset = 40
scale_bar_thickness = 15
# Note: OpenCV uses BGR format, so we need to reverse RGB values
scale_bar_color = (0, 0, 0)


def process_directory(directory_path, scope_type=None):
    """Process all .png images in the given directory."""
    for image_file in glob.glob(os.path.join(directory_path, "*")):
        if not "_scaled" in image_file:
            add_scale_bar(image_file, scope_type)


def detect_scope_type_from_filename(image_path: str) -> str:
    """Detect the scope type from the filename."""
    pattern = r"4X|10X|40X"
    match = re.search(pattern, image_path, flags=re.IGNORECASE)
    return match.group() if match else ""


def add_scale_bar(image_path, scope_type) -> None:
    """Add a scale bar to an image based on the type of scope."""
    if not os.path.exists(image_path):
        print("The image does not exist. Please provide a valid image.")
        return

    if not image_path.lower().endswith(".tif") and not image_path.lower().endswith(
        ".png"
    ):
        print(
            "The image must be in .tif format or .png format. Please provide a valid image."
        )
        return

    # Read the image including the alpha channel
    image = cv2.imread(image_path, -1)

    if image is None or image.shape[0] != 1080 or image.shape[1] != 1920:
        print("The image must be 1920x1080 in size. Please provide a valid image.")
        return

    if not scope_type:
        scope_type = detect_scope_type_from_filename(image_path)
        if not scope_type:
            print(
                "Failed to detect scope type from filename. Please add magnification to the filename or use the proper command-line argument."
            )
            return

    # Define the scale bar size based on the scope_type
    scale_bar_size = 0
    label = ""
    if scope_type == "4X":
        scale_bar_size = int(scale_pixel_4X_100_um * 2)
        label = "200 μm"
    elif scope_type == "10X":
        scale_bar_size = int(scale_pixel_10X_100_um * 2)
        label = "200 μm"
    elif scope_type == "40X":
        scale_bar_size = int(scale_pixel_40X_100_um * 0.5)
        label = "50 μm"
    else:
        print("Invalid scope type. Please use 4X, 10X, or 40X.")
        return

    if not DISPLAY_SCALE_NUMBER:
        label = ""

    # Define the position of the scale bar
    position = (
        image.shape[1] - scale_bar_size - scale_bar_location_x_offset,
        image.shape[0] - scale_bar_location_y_offset,
    )

    # Convert BGR color tuple to RGB for PIL
    rgb_color = scale_bar_color[::-1]  # Reverse the BGR tuple to get RGB

    # Create a copy of the image to avoid modifying the original
    image_with_scale = image.copy()

    # Draw the scale bar using a rectangle
    cv2.rectangle(
        image_with_scale,
        position,
        (position[0] + scale_bar_size, position[1] + scale_bar_thickness),
        color=scale_bar_color,  # Use BGR color for OpenCV
        thickness=-1,
    )

    # Convert from BGR to RGB for PIL
    if len(image_with_scale.shape) == 3:  # Color image
        image_rgb = cv2.cvtColor(image_with_scale, cv2.COLOR_BGR2RGB)
    else:  # Grayscale image
        image_rgb = cv2.cvtColor(image_with_scale, cv2.COLOR_GRAY2RGB)

    pil_image = Image.fromarray(image_rgb)

    # Load a platform-independent font
    if sys.platform == "darwin":  # MacOS
        font_path = os.path.join(os.path.dirname(__file__), "Arial.ttf")
    elif sys.platform == "win32":  # Windows
        font_path = "arial.ttf"
    elif sys.platform.startswith("linux"):  # Linux
        font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    else:
        print(
            "Unsupported operating system. Please run this script on MacOS, Windows, or Linux."
        )
        return

    font = ImageFont.truetype(font_path, scale_bar_font_size)
    draw = ImageDraw.Draw(pil_image)

    # Calculate text width to center it
    text_width = draw.textlength(label, font=font)
    text_position = (
        position[0] + (scale_bar_size - text_width) // 2,
        position[1] - text_position_y_offset,
    )

    # Use RGB color for PIL
    draw.text(text_position, label, font=font, fill=rgb_color)

    # Convert back to Numpy array and BGR for saving
    image_final = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # Save the new image
    output_path = image_path[:-4] + "_scaled.tif"
    cv2.imwrite(output_path, image_final)
    print(f"Scale bar added to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a scale bar to an image or all images in a directory based on the type of scope."
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the image or directory containing images.",
    )
    parser.add_argument(
        "scope_type",
        type=str,
        nargs="?",
        default=None,
        help="Optional. Type of scope (4X, 10X, 40X). If omitted, will try to detect from filename.",
    )

    args = parser.parse_args()

    if os.path.isdir(args.path):
        process_directory(args.path, args.scope_type)
    elif os.path.isfile(args.path):
        add_scale_bar(args.path, args.scope_type)
    else:
        print("The provided path does not exist or is not a valid image or directory.")
