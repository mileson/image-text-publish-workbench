import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import image_assets as assets


class ImageAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)

    def image(self, name, size=(30, 40), color="red", metadata=None):
        path = self.root / name
        with Image.new("RGB", size, color) as image:
            image.save(path, pnginfo=metadata)
        return path

    def test_duplicate_bytes_and_pixels_are_reported_separately(self):
        first = self.image("first.png")
        duplicate = self.root / "duplicate.png"
        duplicate.write_bytes(first.read_bytes())
        meta = PngImagePlugin.PngInfo()
        meta.add_text("test", "different metadata")
        different_bytes = self.image("metadata.png", metadata=meta)
        report = assets.duplicate_report([
            {"id": ident, "path": path} for ident, path in
            (("A", first), ("B", duplicate), ("C", different_bytes))
        ])
        self.assertEqual(report["identical_bytes"], [["A", "B"]])
        self.assertEqual(report["identical_pixels"], [["A", "B", "C"]])
        self.assertTrue(all(p.exists() for p in (first, duplicate, different_bytes)))

    def test_mismatch_fails_before_any_batch_output(self):
        entries = [{"id": "01", "path": self.image("vertical.png")},
                   {"id": "02", "path": self.image("square.png", (40, 40))}]
        with self.assertRaisesRegex(ValueError, "aspect ratio mismatch"):
            assets.normalize_batch(entries, self.root / "result")
        self.assertFalse((self.root / "result").exists())

    def test_cover_crops_and_contain_pads_without_stretch(self):
        with Image.new("RGBA", (40, 40), "red") as source:
            cover, crop = assets.normalized_image(source, 30, 40, "cover")
            contain, pad = assets.normalized_image(source, 30, 40, "contain", "blue")
        self.addCleanup(cover.close)
        self.addCleanup(contain.close)
        self.assertEqual(crop["crop_box"], [5.0, 0.0, 35.0, 40.0])
        self.assertEqual(pad["content_box"], [0, 5, 30, 35])
        self.assertEqual(contain.getpixel((15, 0)), (0, 0, 255, 255))
        self.assertEqual(contain.getpixel((15, 20)), (255, 0, 0, 255))

    def test_exif_orientation_is_applied_before_ratio_check(self):
        path = self.root / "rotated.jpg"
        with Image.new("RGB", (40, 30), "red") as source:
            exif = source.getexif()
            exif[274] = 6
            source.save(path, exif=exif)
        with assets.read_image(path) as source:
            self.assertEqual(source.size, (30, 40))
            result, _ = assets.normalized_image(source, 30, 40)
            result.close()

    def test_normalize_default_size_and_overwrite_protection(self):
        source = self.image("source.png")
        entries = [{"id": "01", "path": source}]
        result = assets.normalize_batch(entries, self.root / "normalized")
        with Image.open(self.root / "normalized/01.png") as image:
            self.assertEqual(image.size, (1080, 1440))
        self.assertEqual(result["images"][0]["source_sha256"], assets.sha256_file(source))
        with self.assertRaisesRegex(ValueError, "already exists"):
            assets.normalize_batch(entries, self.root / "normalized")

    def test_input_ids_and_relative_paths(self):
        self.image("source.png")
        path = self.root / "inputs.json"
        path.write_text(json.dumps({"images": [{"id": "pose003", "path": "source.png"}]}))
        entries = assets.load_entries(path)
        self.assertEqual(entries[0]["id"], "pose003")
        self.assertEqual(entries[0]["path"], self.root / "source.png")
        path.write_text(json.dumps({"images": [{"id": "same", "path": "source.png"}] * 2}))
        with self.assertRaisesRegex(ValueError, "Duplicate ID"):
            assets.load_entries(path)

    def test_contact_and_comparison_sheets_preserve_input_order(self):
        red, blue = self.image("red.png"), self.image("blue.png", color="blue")
        board = assets.make_contact_sheet(
            [{"id": "pose009", "path": blue}, {"id": "pose002", "path": red}],
            self.root / "board.png", cols=2, cell_width=160, cell_height=180)
        with Image.open(board) as image:
            self.assertEqual(image.size, (320, 240))
            self.assertEqual(image.getpixel((80, 90)), (0, 0, 255))
            self.assertEqual(image.getpixel((240, 90)), (255, 0, 0))
        comparison = assets.comparison_sheet(
            [{"id": "pose009", "original": red, "remake": blue}],
            self.root / "compare.png", 160, 180)
        with Image.open(comparison) as image:
            self.assertEqual(image.getpixel((80, 90)), (255, 0, 0))
            self.assertEqual(image.getpixel((240, 90)), (0, 0, 255))
        with self.assertRaisesRegex(ValueError, "already exists"):
            assets.make_contact_sheet([{"id": "x", "path": red}], board)


if __name__ == "__main__":
    unittest.main()
