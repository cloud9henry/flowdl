import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from flowdl.core.watcher import load_watch_state, save_watch_state, watch_interval, watch_once


class WatcherTests(unittest.TestCase):
    def test_load_watch_state_returns_default_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "missing.json"
            state = load_watch_state(state_path)
        self.assertEqual(state, {"sources": {}})

    def test_save_and_load_watch_state_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "watch_state.json"
            original = {"sources": {"u": {"seen_urls": ["a"]}}}
            save_watch_state(original, state_path)
            loaded = load_watch_state(state_path)
        self.assertEqual(loaded, original)

    def test_watch_once_processes_only_new_urls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "watch_state.json"
            save_watch_state(
                {"sources": {"https://example.com/source": {"seen_urls": ["https://example.com/a"]}}},
                state_path,
            )

            with patch(
                "flowdl.core.watcher.get_playlist_urls",
                return_value=["https://example.com/a", "https://example.com/b"],
            ), patch("flowdl.core.watcher.run_pipeline", return_value="/tmp/final.mp4") as run_mock:
                result = watch_once("https://example.com/source", {"mode": "video"}, state_path=state_path)

            self.assertEqual(result["discovered"], 2)
            self.assertEqual(result["new"], 1)
            self.assertEqual(result["processed"], 1)
            self.assertEqual(result["failed"], 0)
            run_mock.assert_called_once_with("https://example.com/b", {"mode": "video"})

    def test_watch_once_tracks_failures_without_marking_seen(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "watch_state.json"

            with patch(
                "flowdl.core.watcher.get_playlist_urls",
                return_value=["https://example.com/a"],
            ), patch("flowdl.core.watcher.run_pipeline", side_effect=RuntimeError("boom")):
                result = watch_once("https://example.com/source", {"mode": "video"}, state_path=state_path)

            self.assertEqual(result["processed"], 0)
            self.assertEqual(result["failed"], 1)
            loaded = load_watch_state(state_path)
            self.assertEqual(loaded["sources"]["https://example.com/source"]["seen_urls"], [])

    def test_watch_interval_rejects_non_positive_interval(self) -> None:
        with self.assertRaises(ValueError):
            watch_interval("https://example.com/source", {"mode": "video"}, interval_minutes=0)

    def test_watch_interval_runs_loop(self) -> None:
        with patch("flowdl.core.watcher.watch_once") as once_mock, patch(
            "flowdl.core.watcher.time.sleep", side_effect=KeyboardInterrupt
        ):
            with self.assertRaises(KeyboardInterrupt):
                watch_interval("https://example.com/source", {"mode": "video"}, interval_minutes=1)
        once_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()

