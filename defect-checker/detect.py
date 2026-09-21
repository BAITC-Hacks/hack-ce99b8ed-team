"""Классификация изображения: OK или DEFECT по доле красных пикселей."""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops


def red_ratio(path: Path) -> float:
    """Доля пикселей, для которых R >= 150, R - G >= 50 и R - B >= 50."""
    with Image.open(path) as source:
        # Прозрачность накладываем на белый фон: скрытый красный не считается.
        rgba = source.convert("RGBA")
        rgb = Image.new("RGB", rgba.size, "white")
        rgb.paste(rgba, mask=rgba.getchannel("A"))

    red, green, blue = rgb.split()
    mask = red.point(lambda value: 255 if value >= 150 else 0)
    for other in (green, blue):
        # Операции над каналами выполняет Pillow, без Python-цикла по пикселям.
        difference = ImageChops.subtract(red, other)
        dominant = difference.point(lambda value: 255 if value >= 50 else 0)
        mask = ImageChops.darker(mask, dominant)

    return mask.histogram()[255] / (rgb.width * rgb.height)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Печатает DEFECT, если доля красного достигает порога, иначе OK."
    )
    parser.add_argument("image", type=Path, help="Путь к изображению")
    parser.add_argument(
        "--threshold", type=float, default=0.10,
        help="Порог доли красного: 0 < значение <= 1 (по умолчанию 0.10)",
    )
    parser.add_argument(
        "--details", action="store_true", help="Показать долю красного в stderr"
    )
    args = parser.parse_args()
    if not 0 < args.threshold <= 1:
        parser.error("--threshold должен быть больше 0 и не больше 1")

    try:
        ratio = red_ratio(args.image)
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        print(f"Ошибка чтения изображения: {exc}", file=sys.stderr)
        return 1

    print("DEFECT" if ratio >= args.threshold else "OK")
    if args.details:
        print(
            f"Красного: {ratio:.2%}; порог: {args.threshold:.2%}", file=sys.stderr
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
