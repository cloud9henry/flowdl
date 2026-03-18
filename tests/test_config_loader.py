import unittest
from pathlib import Path

from flowdl.utils.config_loader import _preset_file_path, get_preset, load_presets
from flowdl.utils.errors import PresetNotFoundError


class ConfigLoaderTests(unittest.TestCase):
    def test_preset_file_path_points_to_presets_json(self) -> None:
        path = _preset_file_path()
        self.assertTrue(path.name == "presets.json")
        self.assertTrue(path.exists())

    def test_load_presets_returns_dict(self) -> None:
        presets = load_presets()
        self.assertIn("music", presets)
        self.assertIn("video", presets)
        self.assertIn("podcast", presets)

    def test_get_preset_returns_selected_preset(self) -> None:
        preset = get_preset("music")
        self.assertEqual(preset["mode"], "audio")

    def test_get_preset_raises_for_missing_name(self) -> None:
        with self.assertRaises(PresetNotFoundError) as ctx:
            get_preset("missing")

        self.assertIn("Available presets", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
