import argparse
import re
import sys
import time
from pathlib import Path

from flowdl.core.downloader import get_playlist_urls
from flowdl.core.pipeline import run_pipeline
from flowdl.core.watcher import watch_once
from flowdl.integrations.ffmpeg_wrapper import trim_media
from flowdl.utils.config_loader import get_preset
from flowdl.utils.errors import DependencyMissingError, FlowDLError, PresetNotFoundError

TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?$")


def _validate_time(value: str) -> str:
    if not TIME_PATTERN.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid time format '{value}'. Use MM:SS or HH:MM:SS."
        )
    return value


def _handle_download(url: str, preset_name: str, playlist: bool = False) -> int:
    try:
        preset = get_preset(preset_name)
        if not playlist:
            final_path = run_pipeline(url, preset)
            print(final_path)
            return 0

        urls = get_playlist_urls(url)
        if not urls:
            print("No items found in playlist.")
            return 0

        failures = 0
        for entry_url in urls:
            try:
                final_path = run_pipeline(entry_url, preset)
                print(f"OK: {entry_url} -> {final_path}")
            except (FlowDLError, RuntimeError) as exc:
                failures += 1
                print(f"FAIL: {entry_url} -> {exc}", file=sys.stderr)

        if failures:
            print(f"Completed with {failures} failure(s).", file=sys.stderr)
            return 1

        print(f"Processed {len(urls)} playlist item(s).")
        return 0
    except (FlowDLError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _handle_batch(file_path: str, preset_name: str) -> int:
    try:
        preset = get_preset(preset_name)
    except PresetNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    path = Path(file_path)
    if not path.exists():
        print(f"Error: Batch file not found: {file_path}", file=sys.stderr)
        return 1

    urls = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not urls:
        print("No URLs found in batch file.")
        return 0

    failures = 0
    for url in urls:
        try:
            final_path = run_pipeline(url, preset)
            print(f"OK: {url} -> {final_path}")
        except (FlowDLError, RuntimeError) as exc:
            failures += 1
            print(f"FAIL: {url} -> {exc}", file=sys.stderr)

    if failures:
        print(f"Completed with {failures} failure(s).", file=sys.stderr)
        return 1

    print(f"Processed {len(urls)} URL(s).")
    return 0


def _handle_trim(file_path: str, start: str, end: str) -> int:
    try:
        result = trim_media(file_path, start=start, end=end)
        print(result)
        return 0
    except (DependencyMissingError, RuntimeError) as exc:
        print(f"Warning: {exc}", file=sys.stderr)
        return 1


def _handle_watch(url: str, preset_name: str, once: bool, interval: int | None) -> int:
    try:
        preset = get_preset(preset_name)
    except PresetNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Default mode is one-off watch execution.
    is_once_mode = once or interval is None
    if is_once_mode:
        try:
            result = watch_once(url, preset)
            print(
                f"Watch run complete: discovered={result['discovered']} new={result['new']} "
                f"processed={result['processed']} failed={result['failed']}"
            )
            return 1 if result["failed"] else 0
        except (FlowDLError, RuntimeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if interval is None or interval <= 0:
        print("Error: --interval must be greater than 0.", file=sys.stderr)
        return 1

    print(f"Watching {url} every {interval} minute(s). Press Ctrl+C to stop.")
    try:
        while True:
            result = watch_once(url, preset)
            print(
                f"Watch cycle: discovered={result['discovered']} new={result['new']} "
                f"processed={result['processed']} failed={result['failed']}"
            )
            time.sleep(interval * 60)
    except KeyboardInterrupt:
        print("Watch stopped.")
        return 0
    except (FlowDLError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flowdl",
        description="Preset-driven media pipeline: download, post-process, organise.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download and process a single URL.")
    download_parser.add_argument("url", help="Media URL to download.")
    download_parser.add_argument("--preset", default="video", help="Preset name from presets.json.")
    download_parser.add_argument(
        "--playlist",
        action="store_true",
        help="Treat URL as playlist/channel feed and process each item with the selected preset.",
    )

    batch_parser = subparsers.add_parser("batch", help="Process a list of URLs from a text file.")
    batch_parser.add_argument("file", help="Path to text file containing one URL per line.")
    batch_parser.add_argument("--preset", default="video", help="Preset name from presets.json.")

    trim_parser = subparsers.add_parser("trim", help="Trim an existing media file with ffmpeg.")
    trim_parser.add_argument("file", help="Input media file.")
    trim_parser.add_argument("--start", required=True, type=_validate_time, help="Start time.")
    trim_parser.add_argument("--end", required=True, type=_validate_time, help="End time.")

    watch_parser = subparsers.add_parser("watch", help="Watch a playlist/channel URL for new items.")
    watch_parser.add_argument("url", help="Playlist or channel URL to monitor.")
    watch_parser.add_argument("--preset", default="video", help="Preset name from presets.json.")
    watch_mode_group = watch_parser.add_mutually_exclusive_group()
    watch_mode_group.add_argument(
        "--once",
        action="store_true",
        help="Run one watch cycle and exit (default behavior).",
    )
    watch_mode_group.add_argument(
        "--interval",
        type=int,
        help="Run continuously, checking for new items every N minutes.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        return _handle_download(args.url, args.preset, args.playlist)

    if args.command == "batch":
        return _handle_batch(args.file, args.preset)

    if args.command == "trim":
        return _handle_trim(args.file, args.start, args.end)

    if args.command == "watch":
        return _handle_watch(args.url, args.preset, args.once, args.interval)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
