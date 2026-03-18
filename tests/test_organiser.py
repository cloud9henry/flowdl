import tempfile
import unittest
from pathlib import Path

from flowdl.core.organiser import organise_output


class OrganiserTests(unittest.TestCase):
    def test_organise_output_moves_file_to_preset_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.mp3"
            source.write_text("data", encoding="utf-8")
            output_dir = Path(tmpdir) / "Downloads" / "Music"

            final_path = organise_output(str(source), {"output_dir": str(output_dir)})

            self.assertTrue(Path(final_path).exists())
            self.assertFalse(source.exists())
            self.assertEqual(Path(final_path).parent, output_dir)

    def test_organise_output_applies_filename_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.mp4"
            source.write_text("data", encoding="utf-8")
            output_dir = Path(tmpdir) / "Downloads" / "Lectures"
            preset = {
                "output_dir": str(output_dir),
                "filename_template": "{uploader}-{title}.{ext}",
            }
            metadata = {"uploader": "MIT OCW", "title": "Week 1 Intro"}

            final_path = organise_output(str(source), preset, metadata=metadata, preset_name="lecture")

            self.assertTrue(Path(final_path).exists())
            self.assertEqual(Path(final_path).name, "MIT OCW-Week 1 Intro.mp4")

    def test_organise_output_avoids_filename_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "Downloads" / "Lectures"
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "Lecture.mp4").write_text("old", encoding="utf-8")

            source = Path(tmpdir) / "source.mp4"
            source.write_text("data", encoding="utf-8")
            preset = {"output_dir": str(output_dir), "filename_template": "{title}.{ext}"}

            final_path = organise_output(str(source), preset, metadata={"title": "Lecture"}, preset_name="lecture")

            self.assertEqual(Path(final_path).name, "Lecture (1).mp4")


if __name__ == "__main__":
    unittest.main()
