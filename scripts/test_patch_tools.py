"""Offline regression checks for working-size controls and pixel protection."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image


SCRIPT = Path(__file__).with_name("patch_tools.py")


class WorkingSizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        Image.new("RGB", (320, 240), (90, 120, 150)).save(self.source)

    def run_tool(self, *args, success=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def prepare(self, name, *options):
        pack = self.root / name
        result = self.run_tool(
            "prepare", self.source, pack,
            "--bbox", "100,80,60,50", "--context-bbox", "60,40,176,176",
            "--work-size", "1536", *options,
        )
        return pack, json.loads(result.stdout)

    def test_default_cap_remains_visible_and_backward_compatible(self):
        pack, report = self.prepare("default")
        self.assertEqual(report["work_size"], [704, 704])
        self.assertTrue(report["work_size_limited"])
        self.assertTrue(any("--max-upscale" in x for x in report["warnings"]))
        manifest = json.loads((pack / "manifest.json").read_text())
        self.assertEqual(manifest["max_upscale"], 4)
        self.assertEqual(manifest["requested_work_size"], 1536)

    def test_explicit_enlargement_preserves_coordinates_and_pixel_gate(self):
        pack, report = self.prepare("detail", "--max-upscale", "12")
        self.assertEqual(report["work_size"], [1536, 1536])
        self.assertFalse(report["work_size_limited"])
        manifest = json.loads((pack / "manifest.json").read_text())
        self.assertEqual(manifest["context_bbox"], [60, 40, 176, 176])
        self.assertEqual(manifest["target_bbox"], [100, 80, 60, 50])
        for name in ("crop-work.png", "mask-hard-work.png", "mask-soft-work.png"):
            with Image.open(pack / name) as image:
                self.assertEqual(image.size, (1536, 1536))
        with Image.open(pack / "crop-native.png") as image:
            self.assertEqual(image.size, (176, 176))
        edited = self.root / "edited.png"
        Image.new("RGB", (1536, 1536), (200, 60, 30)).save(edited)
        output = self.root / "output.png"
        self.run_tool("compose", pack / "manifest.json", edited, output, "--color-match", "0")
        result = self.run_tool("verify", pack / "manifest.json", output, self.root / "qa")
        verification = json.loads(result.stdout)
        self.assertTrue(verification["technical_pass"])
        self.assertFalse(verification["delivery_allowed"])
        self.assertEqual(verification["changed_pixels_outside_soft_mask"], 0)
        with Image.open(output) as image:
            self.assertEqual(image.size, (320, 240))
            self.assertGreater(np.count_nonzero(np.asarray(image) != (90, 120, 150)), 0)

    def test_invalid_scale_controls_fail_before_creating_patch(self):
        for flag, value in (("--max-upscale", "0"), ("--max-upscale", "-1"),
                            ("--max-upscale", "nan"), ("--max-upscale", "inf"),
                            ("--work-size", "0")):
            with self.subTest(flag=flag, value=value):
                output = self.root / (flag.strip("-") + value)
                self.run_tool("prepare", self.source, output, "--bbox", "100,80,60,50",
                              flag, value, success=False)
                self.assertFalse((output / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
