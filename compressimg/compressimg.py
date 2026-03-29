#!/usr/bin/env python3
"""compressimg - Compress images by resolution or percentage while maximizing quality."""

import sys
import argparse
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install it with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def parse_scale(value: str):
    """Parse a scale value: either 'WxH' resolution or 'N%' percentage."""
    value = value.strip()
    if value.endswith("%"):
        pct = float(value[:-1])
        if not (1 <= pct <= 99):
            raise argparse.ArgumentTypeError("Percentage must be between 1 and 99")
        return ("percent", pct)
    if "x" in value.lower():
        parts = value.lower().split("x")
        if len(parts) != 2:
            raise argparse.ArgumentTypeError("Resolution must be WxH (e.g. 1920x1080)")
        w, h = int(parts[0]), int(parts[1])
        return ("resolution", (w, h))
    raise argparse.ArgumentTypeError("Scale must be a percentage (e.g. 50%) or resolution (e.g. 1920x1080)")


def new_size(orig_w: int, orig_h: int, scale) -> tuple[int, int]:
    mode, val = scale
    if mode == "percent":
        factor = val / 100
        return max(1, int(orig_w * factor)), max(1, int(orig_h * factor))
    # resolution: fit within WxH, preserving aspect ratio
    target_w, target_h = val
    ratio = min(target_w / orig_w, target_h / orig_h)
    if ratio >= 1.0:
        # Already smaller than target — only downscale
        return orig_w, orig_h
    return max(1, int(orig_w * ratio)), max(1, int(orig_h * ratio))


def output_path(input_path: Path, output_dir: Optional[Path], suffix: str) -> Path:
    stem = input_path.stem + suffix
    name = stem + input_path.suffix
    base = output_dir if output_dir else input_path.parent
    return base / name


def compress_image(src: Path, dst: Path, scale, quality: int, dry_run: bool) -> dict:
    img = Image.open(src)
    orig_mode = img.mode
    orig_w, orig_h = img.size
    orig_size = src.stat().st_size

    w, h = new_size(orig_w, orig_h, scale)
    resized = w != orig_w or h != orig_h

    if resized:
        img = img.resize((w, h), Image.LANCZOS)

    fmt = img.format or src.suffix.lstrip(".").upper()
    if fmt in ("JPG",):
        fmt = "JPEG"

    save_kwargs = {}
    if fmt == "JPEG":
        # Convert palette/RGBA to RGB for JPEG
        if img.mode in ("RGBA", "P", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
    elif fmt == "PNG":
        # PNG is lossless; optimize compression level (0-9)
        save_kwargs = {"optimize": True, "compress_level": 9}
    elif fmt == "WEBP":
        save_kwargs = {"quality": quality, "method": 6}
    else:
        # Generic fallback
        save_kwargs = {}

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst, format=fmt, **save_kwargs)
        new_size_bytes = dst.stat().st_size
    else:
        new_size_bytes = None

    return {
        "src": src,
        "dst": dst,
        "orig_res": (orig_w, orig_h),
        "new_res": (w, h),
        "orig_size": orig_size,
        "new_size": new_size_bytes,
        "fmt": fmt,
    }


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def print_result(r: dict, dry_run: bool):
    orig_res = f"{r['orig_res'][0]}x{r['orig_res'][1]}"
    new_res  = f"{r['new_res'][0]}x{r['new_res'][1]}"
    res_part = f"{orig_res} -> {new_res}" if r["orig_res"] != r["new_res"] else orig_res

    if dry_run:
        size_part = f"{human(r['orig_size'])} (dry run)"
    else:
        delta_pct = (r["new_size"] - r["orig_size"]) / r["orig_size"] * 100 if r["orig_size"] else 0
        size_part = f"{human(r['orig_size'])} -> {human(r['new_size'])}  ({delta_pct:+.1f}%)"

    dst_label = "[dry run]" if dry_run else str(r["dst"])
    print(f"  {r['src'].name}  [{res_part}]  {size_part}")
    if not dry_run:
        print(f"    -> {dst_label}")


def main():
    parser = argparse.ArgumentParser(
        prog="compressimg",
        description="Compress images by percentage or target resolution while keeping highest quality.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  compressimg photo.jpg -s 50%              # shrink to 50%% of original dimensions
  compressimg photo.jpg -s 1920x1080        # fit within 1920x1080, preserve aspect ratio
  compressimg *.png -s 75% -o compressed/  # batch compress PNGs into a folder
  compressimg photo.jpg -s 50% --dry-run   # preview without writing files
  compressimg photo.jpg -s 1280x720 --suffix _hd  # custom output suffix
        """,
    )
    parser.add_argument("images", nargs="+", metavar="IMAGE", help="Input image file(s)")
    parser.add_argument(
        "-s", "--scale", required=True, metavar="SCALE",
        help="Scale: percentage (e.g. 50%%) or resolution (e.g. 1920x1080)",
    )
    parser.add_argument(
        "-o", "--output-dir", metavar="DIR",
        help="Output directory (default: same directory as input)",
    )
    parser.add_argument(
        "--suffix", default="_compressed", metavar="SUFFIX",
        help="Suffix appended to output filename stem (default: _compressed)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Write output file with the same name as input (overwrites original)",
    )
    parser.add_argument(
        "-q", "--quality", type=int, default=85, metavar="0-100",
        help="Quality for JPEG/WebP (default: 85; PNG is always lossless)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without writing any files",
    )

    args = parser.parse_args()

    try:
        scale = parse_scale(args.scale)
    except argparse.ArgumentTypeError as e:
        parser.error(str(e))

    if not (1 <= args.quality <= 100):
        parser.error("--quality must be between 1 and 100")

    output_dir = Path(args.output_dir) if args.output_dir else None
    errors = 0

    print(f"Scale: {args.scale}  |  Quality: {args.quality}  |  Mode: {'dry-run' if args.dry_run else 'write'}")
    print()

    for pattern in args.images:
        # Support shell-unexpanded globs on some systems
        from glob import glob
        paths = [Path(p) for p in glob(pattern)] or [Path(pattern)]
        for src in paths:
            if not src.exists():
                print(f"  skip: {src} (not found)", file=sys.stderr)
                errors += 1
                continue
            if not src.is_file():
                print(f"  skip: {src} (not a file)", file=sys.stderr)
                continue

            if args.overwrite:
                dst = src
            else:
                dst = output_path(src, output_dir, args.suffix)

            try:
                result = compress_image(src, dst, scale, args.quality, args.dry_run)
                print_result(result, args.dry_run)
            except Exception as e:
                print(f"  error: {src}: {e}", file=sys.stderr)
                errors += 1

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
