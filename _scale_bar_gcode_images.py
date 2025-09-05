from PIL import ImageFont, ImageDraw, Image
import cv2
import numpy as np
import argparse
import os
import sys
import glob

DISPLAY_SCALE_NUMBER = False

# Constants from the calibration of the scopes
scale_pixel_1000_um = 24

scale_bar_location_x_offset = 10
scale_bar_location_y_offset = 35
scale_bar_font_size = 50
text_position_y_offset = 50
scale_bar_thickness = 25
scale_bar_color = (0, 0, 0)


def add_scale_bar(image_path) -> None:
    """Add a scale bar to an image."""

    # Check if the image exists
    if not os.path.exists(image_path):
        print("The image does not exist. Please provide a valid image.")
        return

    # Check the file extension
    if not image_path.lower().endswith(".png"):
        print(f"Skipping {image_path}: The image must be in .png format.")
        return

    # Read the image including the alpha channel
    image = cv2.imread(image_path, -1)

    scale_bar_size = int(scale_pixel_1000_um * 10)
    label = "1 cm"

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
    output_path = image_path[:-4] + "_scaled.png"
    cv2.imwrite(output_path, image)
    print(f"Scale bar added to {output_path}")


def process_directory(directory_path):
    """Process all PNG images in the given directory."""
    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        return

    # Get all PNG files in the directory
    png_files = glob.glob(os.path.join(directory_path, "*.png"))

    if not png_files:
        print(f"No PNG files found in {directory_path}")
        return

    processed_count = 0
    for image_path in png_files:
        # Skip files that already have "_scaled" in their name
        if "_scaled" in image_path:
            continue
        add_scale_bar(image_path)
        processed_count += 1

    print(f"\nProcessing complete: {processed_count} images processed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add a scale bar to an image or all images in a directory."
    )
    parser.add_argument(
        "path",
        type=str,
        help="Path to the image or directory containing images.",
    )

    args = parser.parse_args()

    # Check if the path is a directory or a file
    if os.path.isdir(args.path):
        process_directory(args.path)
    elif os.path.isfile(args.path):
        add_scale_bar(args.path)
    else:
        print("The provided path does not exist or is not a valid image or directory.")
