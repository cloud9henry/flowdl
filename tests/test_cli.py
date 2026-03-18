import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from flowdl.cli.main import (
    _handle_batch,
    _handle_clip,
    _handle_download,
    _handle_watch,
    _handle_trim,
    _parse_timestamps_file,
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
        self.assertFalse(parsed.audio_sidecar)

    def test_build_parser_playlist_flag(self) -> None:
        parser = build_parser()
        parsed = parser.parse_args(["download", "https://example.com/list", "--playlist"])
        self.assertTrue(parsed.playlist)

    def test_build_parser_watch_once_default(self) -> None:
        parser = build_parser()
        parsed = parser.parse_args(["watch", "https://example.com/channel"])
        self.assertEqual(parsed.command, "watch")
        self.assertTrue(parsed.once is False)
        self.assertIsNone(parsed.interval)
        self.assertFalse(parsed.audio_sidecar)

    def test_build_parser_clip_command(self) -> None:
        parser = build_parser()
        parsed = parser.parse_args(["clip", "input.mp4", "--timestamps", "notes.txt"])
        self.assertEqual(parsed.command, "clip")
        self.assertEqual(parsed.timestamps, "notes.txt")

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

        def side_effect(
            url: str,
            preset: dict,
            audio_sidecar: bool = False,
            preset_name: str | None = None,
        ) -> str:
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

            def run_side_effect(
                url: str,
                preset: dict,
                audio_sidecar: bool = False,
                preset_name: str | None = None,
            ) -> str:
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

    def test_handle_watch_once_success(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
            "flowdl.cli.main.watch_once",
            return_value={"discovered": 3, "new": 2, "processed": 2, "failed": 0},
        ):
            with redirect_stdout(stdout):
                code = _handle_watch("https://example.com/channel", "video", once=True, interval=None)

        self.assertEqual(code, 0)
        self.assertIn("Watch run complete", stdout.getvalue())

    def test_handle_watch_once_with_failures_returns_error(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
            "flowdl.cli.main.watch_once",
            return_value={"discovered": 3, "new": 2, "processed": 1, "failed": 1},
        ):
            with redirect_stdout(stdout):
                code = _handle_watch("https://example.com/channel", "video", once=True, interval=None)

        self.assertEqual(code, 1)

    def test_handle_watch_interval_mode_stops_on_keyboard_interrupt(self) -> None:
        stdout = io.StringIO()
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
            "flowdl.cli.main.watch_once",
            return_value={"discovered": 1, "new": 0, "processed": 0, "failed": 0},
        ), patch("flowdl.cli.main.time.sleep", side_effect=KeyboardInterrupt):
            with redirect_stdout(stdout):
                code = _handle_watch("https://example.com/channel", "video", once=False, interval=1)

        self.assertEqual(code, 0)
        self.assertIn("Watch stopped.", stdout.getvalue())

    def test_handle_download_passes_audio_sidecar_flag(self) -> None:
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
            "flowdl.cli.main.run_pipeline", return_value="/tmp/out.mp4"
        ) as pipeline_mock:
            _handle_download("https://example.com", "video", audio_sidecar=True)

        pipeline_mock.assert_called_once_with(
            "https://example.com",
            {"mode": "video"},
            audio_sidecar=True,
            preset_name="video",
        )

    def test_handle_batch_passes_audio_sidecar_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_file = Path(tmpdir) / "urls.txt"
            batch_file.write_text("https://example.com/a\n", encoding="utf-8")

            with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
                "flowdl.cli.main.run_pipeline", return_value="/tmp/out.mp4"
            ) as pipeline_mock:
                _handle_batch(str(batch_file), "video", audio_sidecar=True)

        pipeline_mock.assert_called_once_with(
            "https://example.com/a",
            {"mode": "video"},
            audio_sidecar=True,
            preset_name="video",
        )

    def test_handle_watch_passes_audio_sidecar_flag(self) -> None:
        with patch("flowdl.cli.main.get_preset", return_value={"mode": "video"}), patch(
            "flowdl.cli.main.watch_once",
            return_value={"discovered": 1, "new": 1, "processed": 1, "failed": 0},
        ) as watch_mock:
            _handle_watch("https://example.com/channel", "video", once=True, interval=None, audio_sidecar=True)

        watch_mock.assert_called_once_with(
            "https://example.com/channel",
            {"mode": "video"},
            audio_sidecar=True,
            preset_name="video",
        )

    def test_parse_timestamps_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            notes = Path(tmpdir) / "notes.txt"
            notes.write_text(
                "# comment\n00:10-01:00 intro section\n01:10:00-01:12:30 key-point\n",
                encoding="utf-8",
            )
            result = _parse_timestamps_file(notes)

        self.assertEqual(
            result,
            [("00:10", "01:00", "intro-section"), ("01:10:00", "01:12:30", "key-point")],
        )

    def test_handle_clip_creates_multiple_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "lecture.mp4"
            source.write_text("data", encoding="utf-8")
            notes = Path(tmpdir) / "notes.txt"
            notes.write_text("00:10-01:00 Intro\n01:10-02:00 Deep dive\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch("flowdl.cli.main.trim_media", side_effect=[str(source), str(source)]) as trim_mock:
                with redirect_stdout(stdout):
                    code = _handle_clip(str(source), str(notes))

        self.assertEqual(code, 0)
        self.assertEqual(trim_mock.call_count, 2)
        self.assertIn("Created 2 clip(s).", stdout.getvalue())

    def test_main_routes_to_handlers(self) -> None:
        with patch("flowdl.cli.main._handle_download", return_value=11) as d_mock, patch(
            "flowdl.cli.main._handle_batch", return_value=12
        ) as b_mock, patch("flowdl.cli.main._handle_trim", return_value=13) as t_mock, patch(
            "flowdl.cli.main._handle_watch", return_value=14
        ) as w_mock, patch("flowdl.cli.main._handle_clip", return_value=15) as c_mock:
            self.assertEqual(main(["download", "https://example.com"]), 11)
            self.assertEqual(main(["batch", "/tmp/x.txt"]), 12)
            self.assertEqual(main(["trim", "a.mp4", "--start", "00:01", "--end", "00:02"]), 13)
            self.assertEqual(main(["watch", "https://example.com/channel"]), 14)
            self.assertEqual(main(["clip", "a.mp4", "--timestamps", "notes.txt"]), 15)
        d_mock.assert_called_once_with("https://example.com", "video", False, False)
        b_mock.assert_called_once_with("/tmp/x.txt", "video", False)
        t_mock.assert_called_once()
        w_mock.assert_called_once_with("https://example.com/channel", "video", False, None, False)
        c_mock.assert_called_once_with("a.mp4", "notes.txt")


if __name__ == "__main__":
    unittest.main()
