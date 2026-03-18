import tempfile
import unittest
from pathlib import Path

from flowdl.utils.file_utils import ensure_directory


class FileUtilsTests(unittest.TestCase):
    def test_ensure_directory_creates_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "a" / "b"
            result = ensure_directory(target)
            self.assertTrue(target.exists())
            self.assertEqual(result, target)


if __name__ == "__main__":
    unittest.main()
