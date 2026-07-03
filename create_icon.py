"""Create the DNS Jantex icon - dark rounded square with orange J."""

import sys
sys.path.insert(0, r'C:\temp\pillow')

from PIL import Image, ImageDraw, ImageFont
import os

def create_jantex_icon(output_path: str, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]):
    """Create the DNS Jantex icon."""
    # Create the largest version first
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background (dark gray)
    margin = 8
    radius = 40
    bg_color = (40, 40, 40, 255)

    # Draw the rounded rectangle
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=bg_color
    )

    # Add subtle gradient effect (lighter at top)
    for y in range(margin, size // 2):
        alpha = int(20 * (1 - y / (size // 2)))
        draw.line([(margin, y), (size - margin, y)], fill=(255, 255, 255, alpha))

    # Draw the "J" letter in orange
    orange = (245, 124, 0, 255)  # #F57C00

    # Try to use a bold font
    font_size = 160
    try:
        # Try common Windows fonts
        for font_name in ["Arial Black", "Impact", "Segoe UI Black", "Calibri", "Arial"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except:
                continue
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Get text bounding box
    text = "J"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the text
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1] + 5  # Slight offset down

    # Draw shadow first
    shadow_offset = 3
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0, 80), font=font)

    # Draw the J
    draw.text((x, y), text, fill=orange, font=font)

    # Save as ICO with multiple sizes
    icon_images = []
    for s in sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        icon_images.append(resized)

    # Save as ICO
    icon_images[0].save(
        output_path,
        format="ICO",
        sizes=sizes,
        append_images=icon_images[1:]
    )

    # Also save as PNG for reference
    png_path = output_path.replace(".ico", ".png")
    img.save(png_path, "PNG")

    print(f"Icon created: {output_path}")
    print(f"PNG saved: {png_path}")


if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)
    icon_path = os.path.join(assets_dir, "icon.ico")
    create_jantex_icon(icon_path)
