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


if __name__ == "__main__":
    unittest.main()
