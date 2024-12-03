from PIL import ImageFont, ImageDraw, Image
import cv2
import numpy as np
import argparse
import os
import sys
import re
import glob

# OLYMPUS IX71 scopes
DISPLAY_SCALE_NUMBER = True

# Constants from the calibration of the scopes
scale_pixel_4X_1X_100_um = 53
scale_pixel_10X_1X_100_um = 132
scale_pixel_40X_1X_100_um = 540

scale_bar_location_x_offset = 60
scale_bar_location_y_offset = 80
scale_bar_font_size = 45
text_position_y_offset = 60
scale_bar_thickness = 30
scale_bar_color = (255, 255, 255)


def process_directory(directory_path, scope_type=None):
    """Process all .tif images in the given directory."""
    for image_file in glob.glob(os.path.join(directory_path, "*.tif")):
        if not image_file.endswith("_scaled.tif"):
            add_scale_bar(image_file, scope_type)


def detect_scope_type_from_filename(image_path: str) -> str:
    """Detect the scope type from the filename."""
    # Define a pattern for the scope type in the filename
    pattern = r"4X_1(?:\.6)?X|10X_1(?:\.6)?X|40X_1(?:\.6)?X"
    match = re.search(pattern, image_path, flags=re.IGNORECASE)
    return match.group() if match else ""


def add_scale_bar(image_path, scope_type) -> None:
    """Add a scale bar to an image based on the type of scope."""

    # Check if the image exists
    if not os.path.exists(image_path):
        print("The image does not exist. Please provide a valid image.")
        return

    # Check the file extension
    if not image_path.endswith(".tif"):
        print("The image must be in .tif format. Please provide a valid image.")
        return

    # Read the image including the alpha channel
    image = cv2.imread(image_path, -1)

    # Check the image size
    if image is None or image.shape[0] != 1440 or image.shape[1] != 1920:
        print("The image must be 1920x1440 in size. Please provide a valid image.")
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
    if scope_type == "4X_1X":
        scale_bar_size = int(scale_pixel_4X_1X_100_um * 3)
        label = "300 μm"
    elif scope_type == "4X_1.6X":
        scale_bar_size = int(scale_pixel_4X_1X_100_um * 1.6 * 2)
        label = "200 μm"
    elif scope_type == "10X_1X":
        scale_bar_size = int(scale_pixel_10X_1X_100_um * 1.5)
        label = "150 μm"
    elif scope_type == "10X_1.6X":
        scale_bar_size = int(scale_pixel_10X_1X_100_um * 1.6)
        label = "100 μm"
    elif scope_type == "40X_1X":
        scale_bar_size = int(scale_pixel_40X_1X_100_um * 0.5)
        label = "50 μm"
    elif scope_type == "40X_1.6X":
        scale_bar_size = int(scale_pixel_40X_1X_100_um * 1.6 * 0.3)
        label = "30 μm"
    else:
        print(
            "Invalid scope type. Please use 4X_1X, 4X_1.6X, 10X_1X, 10X_1.6X, 40X_1X, or 40X_1.6X."
        )
        return

    if not DISPLAY_SCALE_NUMBER:
        label = ""

    # Define the position and thickness of the scale bar
    position = (
        image.shape[1] - scale_bar_size - scale_bar_location_x_offset,
        image.shape[0] - scale_bar_location_y_offset,
    )

    # Draw the scale bar using a rectangle
    cv2.rectangle(
        image,
        position,
        (position[0] + scale_bar_size, position[1] + scale_bar_thickness),
        color=scale_bar_color,
        thickness=-1,
    )

    # Convert from BGR to RGB and to PIL
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)

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

    # Draw non-ascii text onto image
    draw = ImageDraw.Draw(pil_image)

    # Calculate text width to center it
    text_width = draw.textlength(label, font=font)
    text_position = (
        position[0] + (scale_bar_size - text_width) // 2,
        position[1] - text_position_y_offset,
    )

    draw.text(text_position, label, font=font, fill=scale_bar_color)

    # Convert back to Numpy array and switch back from RGB to BGR
    image = np.asarray(pil_image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Save the new image
    output_path = image_path[:-4] + "_scaled.tif"
    cv2.imwrite(output_path, image)
    print(f"Scale bar added to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a scale bar to an image or all images in a directory based on the type of scope."
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the .tif image or directory containing .tif images.",
    )
    parser.add_argument(
        "scope_type",
        type=str,
        nargs="?",
        default=None,
        help="Optional. Type of scope (4X_1X, 4X_1.6X, 10X_1X, 10X_1.6X, 40X_1X, 40X_1.6X). If omitted, will try to detect from filename.",
    )

    args = parser.parse_args()

    # Check if the path is a directory or a file
    if os.path.isdir(args.path):
        process_directory(args.path, args.scope_type)
    elif os.path.isfile(args.path):
        add_scale_bar(args.path, args.scope_type)
    else:
        print("The provided path does not exist or is not a valid image or directory.")