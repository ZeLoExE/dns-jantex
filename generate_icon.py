"""
Generate application icon using PIL/Pillow, or create a minimal valid ICO without it.
"""

import struct
from pathlib import Path


def create_ico_with_pillow(output_path: str):
    """Create ICO using Pillow if available."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False

    # Create 32x32 icon
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Blue circle background
    draw.ellipse([2, 2, 30, 30], fill=(0, 120, 212, 255))

    # White "DNS" text approximation - just draw a simple shape
    draw.rectangle([8, 12, 13, 20], fill=(255, 255, 255, 255))  # D
    draw.rectangle([14, 12, 24, 14], fill=(255, 255, 255, 255))  # N top
    draw.rectangle([14, 18, 24, 20], fill=(255, 255, 255, 255))  # N bottom
    draw.rectangle([25, 12, 30, 20], fill=(255, 255, 255, 255))  # S approx

    # Save as ICO with multiple sizes
    img.save(str(output_path), format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"Icon created with Pillow: {output_path}")
    return True


def create_minimal_ico(output_path: str):
    """Create a minimal valid ICO file with solid blue color."""
    # Simple 16x16 ICO with a solid blue square
    width, height = 16, 16
    bpp = 32

    # Create simple pixel data - solid blue with alpha
    # BMP format is bottom-up BGRA
    pixel_data = bytearray()
    for y in range(height):
        for x in range(width):
            # Blue circle with gradient
            cx, cy = width // 2, height // 2
            dx, dy = x - cx, y - cy
            dist = (dx*dx + dy*dy) ** 0.5
            if dist < 7:
                pixel_data.extend([212, 120, 0, 255])  # BGRA blue
            else:
                pixel_data.extend([0, 0, 0, 0])  # transparent

    # AND mask (1 bit per pixel, all zeros = use alpha)
    and_mask_size = ((width + 31) // 32) * 4 * height
    and_mask = bytearray(and_mask_size)

    # BMP info header (BITMAPINFOHEADER)
    bmp_header = struct.pack('<IiiHHIIiiII',
        40,              # biSize
        width,           # biWidth
        height * 2,      # biHeight (doubled for ICO)
        1,               # biPlanes
        bpp,             # biBitCount
        0,               # biCompression (BI_RGB)
        len(pixel_data) + len(and_mask),  # biSizeImage
        0,               # biXPelsPerMeter
        0,               # biYPelsPerMeter
        0,               # biClrUsed
        0                # biClrImportant
    )

    image_data = bytes(bmp_header) + bytes(pixel_data) + bytes(and_mask)

    # ICO header
    ico_header = struct.pack('<HHH', 0, 1, 1)

    # Directory entry
    data_offset = 6 + 16
    dir_entry = struct.pack('<BBBBHHIH',
        width,           # bWidth
        height,          # bHeight
        0,               # bColorCount
        0,               # bReserved
        1,               # wPlanes
        bpp,             # wBitCount
        len(image_data), # dwBytesInRes
        data_offset      # dwOffset
    )

    with open(output_path, 'wb') as f:
        f.write(ico_header)
        f.write(dir_entry)
        f.write(image_data)

    print(f"Minimal icon created: {output_path}")


if __name__ == "__main__":
    assets_dir = Path(__file__).parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    icon_path = assets_dir / "icon.ico"

    if not create_ico_with_pillow(str(icon_path)):
        create_minimal_ico(str(icon_path))
