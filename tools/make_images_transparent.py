"""Remove the connected pale checkerboard background from the supplied PNG assets."""

from collections import deque
from pathlib import Path

from PIL import Image

IMAGE_DIR = Path(__file__).resolve().parent.parent / "app" / "static" / "images"


def is_background(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, _ = pixel
    return min(red, green, blue) >= 220 and max(red, green, blue) - min(red, green, blue) <= 18


def remove_background(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size
    queue = deque()
    seen = bytearray(width * height)

    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))

    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if seen[index] or not is_background(pixels[x, y]):
            continue
        seen[index] = 1
        red, green, blue, _ = pixels[x, y]
        brightness = min(red, green, blue)
        alpha = max(0, min(255, (238 - brightness) * 14))
        pixels[x, y] = (red, green, blue, alpha)
        if x:
            queue.append((x - 1, y))
        if x + 1 < width:
            queue.append((x + 1, y))
        if y:
            queue.append((x, y - 1))
        if y + 1 < height:
            queue.append((x, y + 1))

    image.save(path, optimize=True)


if __name__ == "__main__":
    for image_path in IMAGE_DIR.glob("*.png"):
        remove_background(image_path)
        print(f"processed: {image_path.name}")
