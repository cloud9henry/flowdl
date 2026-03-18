import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

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
        self.assertIn("mobile", presets)

    def test_load_presets_merges_user_presets(self) -> None:
        with TemporaryDirectory() as tmpdir:
            user_file = Path(tmpdir) / "presets.json"
            user_file.write_text(
                '{"lecture":{"mode":"video","resolution":"720","output_dir":"Downloads/Lectures"}}',
                encoding="utf-8",
            )
            with patch("flowdl.utils.config_loader._user_preset_file_path", return_value=user_file):
                presets = load_presets()

        self.assertIn("lecture", presets)
        self.assertEqual(presets["lecture"]["output_dir"], "Downloads/Lectures")

    def test_load_presets_user_preset_overrides_default(self) -> None:
        with TemporaryDirectory() as tmpdir:
            user_file = Path(tmpdir) / "presets.json"
            user_file.write_text(
                '{"music":{"mode":"audio","format":"mp3","output_dir":"Custom/Music"}}',
                encoding="utf-8",
            )
            with patch("flowdl.utils.config_loader._user_preset_file_path", return_value=user_file):
                presets = load_presets()

        self.assertEqual(presets["music"]["output_dir"], "Custom/Music")

    def test_get_preset_returns_selected_preset(self) -> None:
        preset = get_preset("music")
        self.assertEqual(preset["mode"], "audio")

    def test_get_preset_raises_for_missing_name(self) -> None:
        with self.assertRaises(PresetNotFoundError) as ctx:
            get_preset("missing")

        self.assertIn("Available presets", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
