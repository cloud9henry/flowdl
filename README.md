# FlowDL

FlowDL is a preset-driven CLI media pipeline built on top of `yt-dlp` and `ffmpeg`.

download -> post-process -> organise

It is designed to keep commands simple and repeatable by using presets instead of raw downloader flags.

## Highlights

- Preset-first UX for consistent output
- MP4-first video downloads for better compatibility
- Playlist-aware downloads (`--playlist`)
- Lecture workflow support with optional audio sidecar export
- Clip extraction from timestamp files
- Watch mode for automatic polling (`--once` or `--interval`)

## Requirements

- Python 3.10+
- `ffmpeg` installed and available on `PATH`
- `yt-dlp` (installed automatically by `pip install -e .`)

## Installation

```bash
git clone https://github.com/cloud9henry/flowdl.git
cd flowdl
brew install ffmpeg            # macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Best Example: Lecture Workflow

Download lecture video, compress it for portability, and also export audio:

```bash
flowdl download "https://www.youtube.com/watch?v=..." --preset lecture --audio-sidecar
```

Default lecture outputs:
- video: `Downloads/Lectures`
- audio sidecar: `Downloads/Lectures/Audio`

Then generate clips from notes:

```bash
flowdl clip lecture.mp4 --timestamps notes.txt
```

Example `notes.txt`:

```text
00:10-01:00 Intro
01:10:00-01:12:30 Key concept
```

## Commands

- `flowdl download <url> [--preset <name>] [--playlist] [--audio-sidecar]`
- `flowdl batch <file.txt> [--preset <name>] [--audio-sidecar]`
- `flowdl trim <file> --start <time> --end <time>`
- `flowdl clip <file> --timestamps <notes.txt>`
- `flowdl watch <url> [--preset <name>] [--once | --interval <minutes>] [--audio-sidecar]`

## Presets

Built-in presets in `flowdl/config/presets.json`:

- `music`: audio -> MP3, output to `Downloads/Music`
- `video`: MP4-first video, output to `Downloads/Videos`
- `podcast`: audio -> MP3 + compression, output to `Downloads/Podcasts`
- `mobile`: compressed 720p MP4-first video, output to `Downloads/Mobile`
- `lecture`: compressed 720p video, output to `Downloads/Lectures`

## User Presets

User-level presets are supported at:

`~/.config/flowdl/presets.json`

FlowDL loads defaults first, then merges user presets on top (user keys override defaults).

## Watch Modes

Use `watch` for channel/playlist intake:

- `--once`: run one cycle and exit (best for cron/launchd automation)
- `--interval N`: run continuously and poll every `N` minutes

Watch state is stored at `~/.flowdl/watch_state.json`, so previously seen items are skipped.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

## Roadmap

- Naming templates (for example `Uploader - Title`)
- Metadata embedding and loudness normalization presets
- Download archive and retry/backoff policies
- Watch mode hardening (lockfile/single-instance guarantees)
- Packaged distribution (`pipx`, Homebrew tap)

## Contributing

Contributions are welcome. See `CONTRIBUTING.md`.

## License

MIT. See `LICENSE`.
