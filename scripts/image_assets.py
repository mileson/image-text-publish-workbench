#!/usr/bin/env python3
"""Authorized image housekeeping; never generates or semantically edits images.

Input: JSON images/pairs lists with stable IDs and paths relative to the list.
Output: duplicate reports, aspect-preserving PNGs, contact sheets, comparisons.
Dependencies: Python 3.9+, existing Pillow. Processing is serial and bounded.
"""

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps


MAX_BOARD_PIXELS = 40_000_000
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")


def check_id(value):
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise ValueError("IDs must be 1–80 ASCII letters, digits, underscores or hyphens.")
    return value


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_image(path):
    with Image.open(path) as opened:
        if opened.width * opened.height > MAX_BOARD_PIXELS:
            raise ValueError("Input exceeds 40 million pixels; use an explicitly approved smaller source.")
        return ImageOps.exif_transpose(opened).convert("RGBA")


def resolve_input(raw, base):
    path = Path(raw).expanduser()
    path = path if path.is_absolute() else base / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Input image is missing: {path}")
    return path


def load_entries(list_path=None, input_paths=None, pairs=False):
    if list_path:
        list_path = Path(list_path).expanduser().resolve()
        data = json.loads(list_path.read_text(encoding="utf-8"))
        key = "pairs" if pairs else "images"
        raw_entries = data if isinstance(data, list) else data.get(key, [])
        base = list_path.parent
    else:
        raw_entries = [{"id": Path(p).stem, "path": p} for p in input_paths or []]
        base = Path.cwd()
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("Provide a non-empty images/pairs list or --input files.")
    entries, seen = [], set()
    for item in raw_entries:
        if not isinstance(item, dict):
            raise ValueError("Each list item must be an object with a stable id.")
        ident = check_id(item.get("id"))
        if ident in seen:
            raise ValueError(f"Duplicate ID: {ident}")
        seen.add(ident)
        entry = dict(item)
        for key in (("original", "remake") if pairs else ("path",)):
            if not isinstance(item.get(key), str):
                raise ValueError(f"Missing {key} for {ident}")
            entry[key] = resolve_input(item[key], base)
        entries.append(entry)
    return entries


def new_output(path):
    path = Path(path).expanduser().resolve()
    if path.exists():
        raise ValueError(f"Refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, data):
    path = new_output(path)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def save_png(image, path):
    path = new_output(path)
    if path.suffix.lower() != ".png":
        raise ValueError("Image outputs must use a .png extension.")
    with path.open("xb") as stream:
        image.save(stream, format="PNG")
    return path


def duplicate_report(entries):
    byte_groups, pixel_groups, rows = defaultdict(list), defaultdict(list), []
    for entry in entries:
        digest = sha256_file(entry["path"])
        with read_image(entry["path"]) as image:
            pixel_digest = hashlib.sha256(
                f"RGBA:{image.width}x{image.height}:".encode() + image.tobytes()
            ).hexdigest()
            size = list(image.size)
        byte_groups[digest].append(entry["id"])
        pixel_groups[pixel_digest].append(entry["id"])
        rows.append({"id": entry["id"], "path": str(entry["path"]),
                     "size": size, "sha256": digest, "pixel_sha256": pixel_digest})
    return {"image_count": len(entries), "unique_bytes": len(byte_groups),
            "identical_bytes": [ids for ids in byte_groups.values() if len(ids) > 1],
            "identical_pixels": [ids for ids in pixel_groups.values() if len(ids) > 1],
            "note": "Exact bytes and decoded pixels only; no visual-similarity inference or deletion.",
            "images": rows}


def normalized_image(image, width=1080, height=1440, mode="strict", background="white"):
    if width < 1 or height < 1 or width * height > MAX_BOARD_PIXELS:
        raise ValueError("Target dimensions must be positive and at most 40 million pixels.")
    if mode not in {"strict", "cover", "contain"}:
        raise ValueError("Mode must be strict, cover or contain.")
    sw, sh = image.size
    same_ratio = sw * height == sh * width
    if mode == "strict" and not same_ratio:
        raise ValueError(f"Aspect ratio {sw}:{sh} differs from {width}:{height}; explicitly choose cover (crop) or contain (pad).")
    crop = [0.0, 0.0, float(sw), float(sh)]
    if mode == "cover" and not same_ratio:
        if sw * height > sh * width:
            crop_width = sh * width / height
            crop = [(sw - crop_width) / 2, 0.0, (sw + crop_width) / 2, float(sh)]
        else:
            crop_height = sw * height / width
            crop = [0.0, (sh - crop_height) / 2, float(sw), (sh + crop_height) / 2]
    if mode != "contain" or same_ratio:
        result = image.resize((width, height), Image.Resampling.LANCZOS, box=tuple(crop))
        content_box = [0, 0, width, height]
    else:
        scale = min(width / sw, height / sh)
        size = (max(1, round(sw * scale)), max(1, round(sh * scale)))
        resized = image.resize(size, Image.Resampling.LANCZOS)
        result = Image.new("RGBA", (width, height), ImageColor.getcolor(background, "RGBA"))
        left, top = (width - size[0]) // 2, (height - size[1]) // 2
        result.alpha_composite(resized, (left, top))
        resized.close()
        content_box = [left, top, left + size[0], top + size[1]]
    return result, {"mode": mode, "source_size": [sw, sh], "output_size": [width, height],
                    "crop_box": crop, "content_box": content_box,
                    "background": background if mode == "contain" else None}


def normalize_batch(entries, output_dir, width=1080, height=1440, mode="strict", background="white"):
    output_dir = Path(output_dir).expanduser().resolve()
    # Preflight every input and collision before creating any output.
    for entry in entries:
        check_id(entry["id"])
        for name in (f'{entry["id"]}.png', "manifest.json"):
            if (output_dir / name).exists():
                raise ValueError(f"Output already exists: {output_dir / name}")
        with read_image(entry["path"]) as source:
            if mode == "strict" and source.width * height != source.height * width:
                raise ValueError(f'{entry["id"]}: aspect ratio mismatch; explicitly choose --mode cover or contain.')
    rows = []
    for entry in entries:
        with read_image(entry["path"]) as source:
            result, transform = normalized_image(source, width, height, mode, background)
            target = save_png(result, output_dir / f'{entry["id"]}.png')
            result.close()
        rows.append({"id": entry["id"], "path": target.name,
                     "source_path": str(entry["path"]), "source_sha256": sha256_file(entry["path"]),
                     "sha256": sha256_file(target), "transform": transform})
    write_json(output_dir / "manifest.json", {"images": rows})
    return {"output_dir": str(output_dir), "image_count": len(rows), "images": rows}


def load_font(size):
    for candidate in ("/System/Library/Fonts/Hiragino Sans GB.ttc",
                      "/System/Library/Fonts/Supplemental/Arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def label_lines(draw, text, font, width, limit=2):
    lines, line = [], ""
    for character in text:
        if draw.textbbox((0, 0), line + character, font=font)[2] > width and line:
            lines.append(line)
            line = character
            if len(lines) == limit:
                lines[-1] = lines[-1][:-3] + "..."
                return lines
        else:
            line += character
    if line:
        lines.append(line)
    return lines[:limit]


def make_contact_sheet(entries, output, cols=3, cell_width=360, cell_height=480,
                       title="Reference gallery", labels=None):
    if not entries or cols < 1 or cell_width < 160 or cell_height < 160:
        raise ValueError("Use non-empty inputs, positive columns and cells of at least 160 px.")
    if len(entries) > 100:
        raise ValueError("At most 100 images per sheet; split the input list into batches.")
    rows = math.ceil(len(entries) / cols)
    canvas_size = (cols * cell_width, rows * cell_height + 60)
    if canvas_size[0] * canvas_size[1] > MAX_BOARD_PIXELS:
        raise ValueError("Contact sheet exceeds 40 million pixels; reduce cells or split the list.")
    if Path(output).expanduser().exists():
        raise ValueError(f"Output already exists: {output}")
    canvas = Image.new("RGB", canvas_size, "#f3f0ea")
    draw = ImageDraw.Draw(canvas)
    font, title_font = load_font(17), load_font(24)
    draw.text((16, 15), title, fill="#222222", font=title_font)
    for index, entry in enumerate(entries):
        row, col = divmod(index, cols)
        x, y = col * cell_width, 60 + row * cell_height
        with read_image(entry["path"]) as source:
            source.thumbnail((cell_width - 24, cell_height - 90), Image.Resampling.LANCZOS)
            position = (x + (cell_width - source.width) // 2, y + 10)
            canvas.paste(source, position, source)
        label = labels[index] if labels else f'{entry["id"]}  {entry.get("title", "")}'
        for line_no, line in enumerate(label_lines(draw, label, font, cell_width - 24)):
            draw.text((x + 12, y + cell_height - 65 + line_no * 25), line, fill="#222222", font=font)
    target = save_png(canvas, output)
    canvas.close()
    return target


def comparison_sheet(pairs, output, cell_width=450, cell_height=600, title="Original / Remake"):
    entries, labels = [], []
    for pair in pairs:
        for role in ("original", "remake"):
            entries.append({"id": pair["id"], "path": pair[role]})
            labels.append(f'{pair["id"]} · {role}')
    return make_contact_sheet(entries, output, 2, cell_width, cell_height, title, labels)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("dedupe", "normalize", "contact-sheet"):
        command = sub.add_parser(name)
        group = command.add_mutually_exclusive_group(required=True)
        group.add_argument("--list", help='JSON list or {"images":[{"id":"01","path":"photo.jpg"}]}')
        group.add_argument("--input", action="append", help="Repeat for explicit files; filename stems become IDs.")
    sub.choices["dedupe"].add_argument("--output", help="Optional report JSON, never deletes images.")
    normal = sub.choices["normalize"]
    normal.add_argument("--output-dir", required=True)
    normal.add_argument("--width", type=int, default=1080)
    normal.add_argument("--height", type=int, default=1440)
    normal.add_argument("--mode", choices=("strict", "cover", "contain"), default="strict")
    normal.add_argument("--background", default="white")
    sheet = sub.choices["contact-sheet"]
    sheet.add_argument("--cols", type=int, default=3)
    compare = sub.add_parser("compare")
    compare.add_argument("--list", required=True, help='{"pairs":[{"id":"01","original":"a.jpg","remake":"b.png"}]}')
    for command in (sheet, compare):
        command.add_argument("--output", required=True)
        command.add_argument("--cell-width", type=int, default=360)
        command.add_argument("--cell-height", type=int, default=480)
        command.add_argument("--title", default="")
    args = parser.parse_args(argv)
    try:
        entries = load_entries(args.list, getattr(args, "input", None), args.command == "compare")
        if args.command == "dedupe":
            result = duplicate_report(entries)
            if args.output:
                write_json(args.output, result)
        elif args.command == "normalize":
            result = normalize_batch(entries, args.output_dir, args.width, args.height, args.mode, args.background)
        elif args.command == "contact-sheet":
            path = make_contact_sheet(entries, args.output, args.cols, args.cell_width, args.cell_height, args.title or "Contact sheet")
            result = {"output": str(path), "ids": [e["id"] for e in entries]}
        else:
            path = comparison_sheet(entries, args.output, args.cell_width, args.cell_height, args.title or "Original / Remake")
            result = {"output": str(path), "ids": [e["id"] for e in entries]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"Error: {error}\n")


if __name__ == "__main__":
    main()
