import tempfile
import unittest
from pathlib import Path

from flowdl.utils.naming import ensure_unique_path, render_filename_template, sanitize_filename


class NamingTests(unittest.TestCase):
    def test_sanitize_filename_replaces_invalid_chars(self) -> None:
        self.assertEqual(sanitize_filename('A/B:C*D?"E<F>G|'), "A-B-C-D--E-F-G-")

    def test_render_filename_template_with_metadata(self) -> None:
        name = render_filename_template(
            "{uploader} - {title}.{ext}",
            metadata={"uploader": "MIT OCW", "title": "Lecture 1"},
            preset_name="lecture",
            source_file_path="/tmp/in.mp4",
        )
        self.assertEqual(name, "MIT OCW - Lecture 1.mp4")

    def test_render_filename_template_unknown_key_fails(self) -> None:
        with self.assertRaises(RuntimeError):
            render_filename_template(
                "{unknown}.{ext}",
                metadata={},
                preset_name="video",
                source_file_path="/tmp/in.mp4",
            )

    def test_ensure_unique_path_adds_increment_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "name.mp4"
            first.write_text("x", encoding="utf-8")
            unique = ensure_unique_path(first)
        self.assertEqual(unique.name, "name (1).mp4")


if __name__ == "__main__":
    unittest.main()

