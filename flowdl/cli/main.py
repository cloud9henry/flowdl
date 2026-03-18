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
CLIP_LINE_PATTERN = re.compile(
    r"^\s*(?P<start>\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s+(?P<label>.+))?\s*$"
)


def _validate_time(value: str) -> str:
    if not TIME_PATTERN.match(value):
        raise argparse.ArgumentTypeError(
            f"Invalid time format '{value}'. Use MM:SS or HH:MM:SS."
        )
    return value


def _handle_download(
    url: str,
    preset_name: str,
    playlist: bool = False,
    audio_sidecar: bool = False,
) -> int:
    try:
        preset = get_preset(preset_name)
        if not playlist:
            final_path = run_pipeline(
                url,
                preset,
                audio_sidecar=audio_sidecar,
                preset_name=preset_name,
            )
            print(final_path)
            return 0

        urls = get_playlist_urls(url)
        if not urls:
            print("No items found in playlist.")
            return 0

        failures = 0
        for entry_url in urls:
            try:
                final_path = run_pipeline(
                    entry_url,
                    preset,
                    audio_sidecar=audio_sidecar,
                    preset_name=preset_name,
                )
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


def _handle_batch(file_path: str, preset_name: str, audio_sidecar: bool = False) -> int:
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
            final_path = run_pipeline(
                url,
                preset,
                audio_sidecar=audio_sidecar,
                preset_name=preset_name,
            )
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


def _sanitize_label(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-").lower()


def _parse_timestamps_file(path: Path) -> list[tuple[str, str, str]]:
    if not path.exists():
        raise RuntimeError(f"Timestamps file not found: {path}")

    clip_specs: list[tuple[str, str, str]] = []
    for idx, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = CLIP_LINE_PATTERN.match(line)
        if not match:
            raise RuntimeError(
                f"Invalid timestamp line {idx}: '{raw_line}'. "
                "Use 'START-END [optional label]'."
            )

        start = _validate_time(match.group("start"))
        end = _validate_time(match.group("end"))
        label = match.group("label") or f"clip-{len(clip_specs) + 1:03d}"
        clip_specs.append((start, end, _sanitize_label(label) or f"clip-{len(clip_specs) + 1:03d}"))

    return clip_specs


def _handle_clip(file_path: str, timestamps_file: str) -> int:
    source = Path(file_path)
    if not source.exists():
        print(f"Error: Input file not found: {file_path}", file=sys.stderr)
        return 1

    try:
        specs = _parse_timestamps_file(Path(timestamps_file))
    except (RuntimeError, argparse.ArgumentTypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not specs:
        print("No clip ranges found in timestamps file.")
        return 0

    failures = 0
    for idx, (start, end, label) in enumerate(specs, start=1):
        output_name = f"{source.stem}.clip-{idx:03d}-{label}{source.suffix}"
        output_path = source.with_name(output_name)
        try:
            result = trim_media(str(source), start=start, end=end, output_file=str(output_path))
            print(f"OK: {start}-{end} -> {result}")
        except (DependencyMissingError, RuntimeError) as exc:
            failures += 1
            print(f"FAIL: {start}-{end} -> {exc}", file=sys.stderr)

    if failures:
        print(f"Completed with {failures} failure(s).", file=sys.stderr)
        return 1

    print(f"Created {len(specs)} clip(s).")
    return 0


def _handle_watch(
    url: str,
    preset_name: str,
    once: bool,
    interval: int | None,
    audio_sidecar: bool = False,
) -> int:
    try:
        preset = get_preset(preset_name)
    except PresetNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Default mode is one-off watch execution.
    is_once_mode = once or interval is None
    if is_once_mode:
        try:
            result = watch_once(
                url,
                preset,
                audio_sidecar=audio_sidecar,
                preset_name=preset_name,
            )
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
            result = watch_once(
                url,
                preset,
                audio_sidecar=audio_sidecar,
                preset_name=preset_name,
            )
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
    download_parser.add_argument(
        "--audio-sidecar",
        action="store_true",
        help="For video presets, also export an audio-only sidecar file.",
    )

    batch_parser = subparsers.add_parser("batch", help="Process a list of URLs from a text file.")
    batch_parser.add_argument("file", help="Path to text file containing one URL per line.")
    batch_parser.add_argument("--preset", default="video", help="Preset name from presets.json.")
    batch_parser.add_argument(
        "--audio-sidecar",
        action="store_true",
        help="For video presets, also export an audio-only sidecar file for each item.",
    )

    trim_parser = subparsers.add_parser("trim", help="Trim an existing media file with ffmpeg.")
    trim_parser.add_argument("file", help="Input media file.")
    trim_parser.add_argument("--start", required=True, type=_validate_time, help="Start time.")
    trim_parser.add_argument("--end", required=True, type=_validate_time, help="End time.")

    clip_parser = subparsers.add_parser("clip", help="Create multiple clips from timestamps file.")
    clip_parser.add_argument("file", help="Input media file.")
    clip_parser.add_argument(
        "--timestamps",
        required=True,
        help="Path to timestamp file with lines like '00:10-01:00 Intro section'.",
    )

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
    watch_parser.add_argument(
        "--audio-sidecar",
        action="store_true",
        help="For video presets, also export an audio-only sidecar file.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        return _handle_download(args.url, args.preset, args.playlist, args.audio_sidecar)

    if args.command == "batch":
        return _handle_batch(args.file, args.preset, args.audio_sidecar)

    if args.command == "trim":
        return _handle_trim(args.file, args.start, args.end)

    if args.command == "clip":
        return _handle_clip(args.file, args.timestamps)

    if args.command == "watch":
        return _handle_watch(args.url, args.preset, args.once, args.interval, args.audio_sidecar)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
