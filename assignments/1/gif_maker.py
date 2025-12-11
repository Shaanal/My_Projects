from PIL import Image, ImageDraw, ImageFont
import glob
import cv2
import numpy as np

# Initialize some settings
image_folder = "figures/deg1"
output_gif_path = "figures_gif/degree_1.gif"
duration_per_frame = 100  # milliseconds

# Collect all image paths
image_paths = glob.glob(f"{image_folder}*.jpg")
print(image_paths)
image_paths.sort()  # Sort the images to maintain sequence; adjust as needed

# Initialize an empty list to store the images
frames = []

# Debugging lines (moved here, after frames is initialized)
print("Number of frames: ", len(frames))
print("Image Paths: ", image_paths)

# Loop through each image file to add text and append to frames
for image_path in image_paths:
    img = Image.open(image_path)

    # Reduce the frame size by 50%
    img = img.resize((int(img.width * 0.5), int(img.height * 0.5)))

    # Create a new draw object after resizing
    draw = ImageDraw.Draw(img)

    # Text to display at top-left and bottom-right corners
    top_left_text = image_path.split("/")[-1]
    bottom_right_text = "Add your test here to be displayed on Images"

    # Font settings
    font_path = "/Library/Fonts/Arial.ttf"  # Replace with the path to a .ttf file on your system
    font_size = 20
    font = ImageFont.truetype(font_path, font_size)

    # Draw top-left text
    draw.text((10, 10), top_left_text, font=font, fill=(255, 255, 255))

    # Calculate x, y position of the bottom-right text
    text_width, text_height = draw.textsize(bottom_right_text, font=font)
    x = img.width - text_width - 10  # 10 pixels from the right edge
    y = img.height - text_height - 10  # 10 pixels from the bottom edge

    # Draw bottom-right text
    draw.text((x, y), bottom_right_text, font=font, fill=(255, 255, 255))

    frames.append(img)
    

# Initialize video writer
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or use 'XVID'
out = cv2.VideoWriter('animated_presentation.mp4', fourcc, 20.0, (int(img.width), int(img.height)))

# Loop through each image frame (assuming you have the frames in 'frames' list)
for img_pil in frames:
    # Convert PIL image to numpy array (OpenCV format)
    img_np = np.array(img_pil)

    # Convert RGB to BGR (OpenCV uses BGR instead of RGB)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    # Write frame to video
    out.write(img_bgr)

# Release the VideoWriter
out.release()

# Save frames as an animated GIF
frames[0].save(output_gif_path,
               save_all=True,
               append_images=frames[1:],
               duration=duration_per_frame,
               loop=0,
               optimize=True)
