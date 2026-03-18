# FlowDL

FlowDL is a preset-driven CLI that wraps `yt-dlp` and `ffmpeg` into a clean local pipeline:

download -> post-process -> organise

No raw downloader flags. No giant command strings. Just presets.

## Why FlowDL

- Preset-first UX for repeatable output
- Single command for download + conversion + folder routing
- Playlist-aware downloads with per-item processing
- Minimal dependency surface and macOS-friendly workflow
- Modular Python architecture that is easy to extend

## Use Cases

- Build a podcast library from long-form YouTube content
- Build a cleaner music library from videos/live sets/remixes
- Batch process research or study URLs into consistent outputs
- Trim downloaded media into reusable clips

## Requirements

- Python 3.10+
- `ffmpeg` installed and available on `PATH`
- `yt-dlp` is installed automatically via `pip install -e .`

## Installation

### 1) Clone

```bash
git clone https://github.com/cloud9henry/flowdl.git
cd flowdl
```

### 2) Install ffmpeg (macOS)

```bash
brew install ffmpeg
```

### 3) Create virtualenv and install FlowDL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
flowdl download "https://www.youtube.com/watch?v=jNQXAC9IVRw" --preset music
flowdl download "https://www.youtube.com/playlist?list=..." --preset podcast --playlist
flowdl batch urls.txt --preset podcast
flowdl trim input.mp4 --start 00:10 --end 01:00
flowdl watch "https://www.youtube.com/playlist?list=..." --preset podcast --once
flowdl watch "https://www.youtube.com/@channel/videos" --preset podcast --interval 30
```

## When To Use `watch`

Use `watch` for ongoing intake from a playlist/channel URL.

- Use `--once` when running on a schedule (recommended for most users).
- Use `--interval <minutes>` when you want a continuous foreground watcher.
- Watch state is persisted in `~/.flowdl/watch_state.json`, so already-seen items are skipped on later runs.

## Commands

- `flowdl download <url> [--preset <name>] [--playlist]`
- `flowdl batch <file.txt> [--preset <name>]`
- `flowdl trim <file> --start <time> --end <time>`
- `flowdl watch <url> [--preset <name>] [--once | --interval <minutes>]`

## Presets

Default presets are in `flowdl/config/presets.json`:

- `music`: audio -> MP3, high quality, output to `Downloads/Music`
- `video`: video mode, output to `Downloads/Videos`
- `podcast`: audio -> MP3 + compression, output to `Downloads/Podcasts`
- `mobile`: video preset optimized for smaller files (720p + compression), output to `Downloads/Mobile`

Create additional presets by editing `flowdl/config/presets.json`.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Project layout:

```text
flowdl/
  cli/            # command parsing and handlers
  core/           # pipeline orchestration
  integrations/   # yt-dlp and ffmpeg wrappers
  config/         # default presets
  utils/          # shared helpers and errors
tests/
```

## Roadmap

- Channel/watch mode for automatic polling
- Rich naming templates and metadata embedding
- More output presets (lecture, mobile, creator)

## Contributing

Contributions are welcome. Please read `CONTRIBUTING.md` and open an issue for major changes.

## License

MIT. See `LICENSE`.
