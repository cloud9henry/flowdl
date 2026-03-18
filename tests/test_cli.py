import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from flowdl.cli.main import (
    _handle_batch,
    _handle_download,
    _handle_trim,
    _validate_time,
    build_parser,
    main,
)
from flowdl.utils.errors import DependencyMissingError, FlowDLError, PresetNotFoundError


class CLITests(unittest.TestCase):
    def test_validate_time_accepts_mm_ss_and_hh_mm_ss(self) -> None:
        self.assertEqual(_validate_time("00:10"), "00:10")
        self.assertEqual(_validate_time("01:02:03"), "01:02:03")

    def test_validate_time_rejects_invalid(self) -> None:
        with self.assertRaises(argparse.ArgumentTypeError):
            _validate_time("10")

    def test_build_parser_has_expected_commands(self) -> None:
        parser = build_parser()
        parsed = parser.parse_args(["download", "https://example.com"])
        self.assertEqual(parsed.command, "download")
        self.assertEqual(parsed.preset, "video")
        self.assertFalse(parsed.playlist)

    def test_build_parser_playlist_flag(self) -> None:
        parser = build_parser()
        parsed = parser.parse_args(["download", "https://example.com/list", "--playlist"])
        self.assertTrue(parsed.playlist)

    def test_handle_download_success(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "audio"}), patch(
            "flowdl.cli.main.run_pipeline", return_value="/tmp/out.mp3"
        ):
            with redirect_stdout(stdout):
                code = _handle_download("https://example.com", "music")

        self.assertEqual(code, 0)
        self.assertIn("/tmp/out.mp3", stdout.getvalue())

    def test_handle_download_handles_errors(self) -> None:
        stderr = io.StringIO()
        with patch("flowdl.cli.main.get_preset", side_effect=PresetNotFoundError("missing")):
            with redirect_stderr(stderr):
                code = _handle_download("https://example.com", "music")

        self.assertEqual(code, 1)
        self.assertIn("Error:", stderr.getvalue())

    def test_handle_download_playlist_success(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "audio"}), patch(
            "flowdl.cli.main.get_playlist_urls",
            return_value=["https://example.com/a", "https://example.com/b"],
        ), patch("flowdl.cli.main.run_pipeline", return_value="/tmp/out.mp3"):
            with redirect_stdout(stdout):
                code = _handle_download("https://example.com/list", "music", playlist=True)

        self.assertEqual(code, 0)
        self.assertIn("Processed 2 playlist item(s).", stdout.getvalue())

    def test_handle_download_playlist_partial_failure(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        def side_effect(url: str, preset: dict) -> str:
            if url.endswith("/b"):
                raise RuntimeError("bad")
            return "/tmp/out.mp3"

        with patch("flowdl.cli.main.get_preset", return_value={"mode": "audio"}), patch(
            "flowdl.cli.main.get_playlist_urls",
            return_value=["https://example.com/a", "https://example.com/b"],
        ), patch("flowdl.cli.main.run_pipeline", side_effect=side_effect):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = _handle_download("https://example.com/list", "music", playlist=True)

        self.assertEqual(code, 1)
        self.assertIn("Completed with 1 failure(s).", stderr.getvalue())

    def test_handle_download_playlist_empty(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "audio"}), patch(
            "flowdl.cli.main.get_playlist_urls",
            return_value=[],
        ):
            with redirect_stdout(stdout):
                code = _handle_download("https://example.com/list", "music", playlist=True)

        self.assertEqual(code, 0)
        self.assertIn("No items found in playlist.", stdout.getvalue())

    def test_handle_batch_missing_file(self) -> None:
        stderr = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}):
            with redirect_stderr(stderr):
                code = _handle_batch("/tmp/does-not-exist.txt", "video")

        self.assertEqual(code, 1)
        self.assertIn("Batch file not found", stderr.getvalue())

    def test_handle_batch_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_file = Path(tmpdir) / "urls.txt"
            batch_file.write_text("\n# comment only\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}):
                with redirect_stdout(stdout):
                    code = _handle_batch(str(batch_file), "video")

        self.assertEqual(code, 0)
        self.assertIn("No URLs found", stdout.getvalue())

    def test_handle_batch_processes_and_tracks_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_file = Path(tmpdir) / "urls.txt"
            batch_file.write_text("https://example.com/a\nhttps://example.com/b\n", encoding="utf-8")

            def run_side_effect(url: str, preset: dict) -> str:
                if url.endswith("b"):
                    raise FlowDLError("bad")
                return "/tmp/out.mp4"

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
                "flowdl.cli.main.run_pipeline", side_effect=run_side_effect
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = _handle_batch(str(batch_file), "video")

        self.assertEqual(code, 1)
        self.assertIn("OK:", stdout.getvalue())
        self.assertIn("Completed with 1 failure(s)", stderr.getvalue())

    def test_handle_trim_success(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.trim_media", return_value="/tmp/in.trimmed.mp4"):
            with redirect_stdout(stdout):
                code = _handle_trim("/tmp/in.mp4", "00:01", "00:10")

        self.assertEqual(code, 0)
        self.assertIn("trimmed", stdout.getvalue())

    def test_handle_trim_warning_on_error(self) -> None:
        stderr = io.StringIO()
        with patch("flowdl.cli.main.trim_media", side_effect=DependencyMissingError("ffmpeg missing")):
            with redirect_stderr(stderr):
                code = _handle_trim("/tmp/in.mp4", "00:01", "00:10")

        self.assertEqual(code, 1)
        self.assertIn("Warning:", stderr.getvalue())

    def test_main_routes_to_handlers(self) -> None:
        with patch("flowdl.cli.main._handle_download", return_value=11) as d_mock, patch(
            "flowdl.cli.main._handle_batch", return_value=12
        ) as b_mock, patch("flowdl.cli.main._handle_trim", return_value=13) as t_mock:
            self.assertEqual(main(["download", "https://example.com"]), 11)
            self.assertEqual(main(["batch", "/tmp/x.txt"]), 12)
            self.assertEqual(main(["trim", "a.mp4", "--start", "00:01", "--end", "00:02"]), 13)

        d_mock.assert_called_once_with("https://example.com", "video", False)
        b_mock.assert_called_once()
        t_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
