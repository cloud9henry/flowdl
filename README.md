# FlowDL

FlowDL is a preset-driven local CLI media pipeline built on top of `yt-dlp` and `ffmpeg`.

## Features

- Preset-first UX (no raw `yt-dlp` flags in CLI)
- Pipeline flow: download -> post-process -> organise
- Simple command surface for single URL, batch files, and trimming
- Modular Python architecture designed for extension

## Requirements

- Python 3.10+
- `ffmpeg` installed and available on `PATH`

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

```bash
flowdl download "https://www.youtube.com/watch?v=jNQXAC9IVRw" --preset music
flowdl batch urls.txt --preset podcast
flowdl trim input.mp4 --start 00:10 --end 01:00
```

## CLI Commands

- `flowdl download <url> [--preset <name>]`
- `flowdl batch <file.txt> [--preset <name>]`
- `flowdl trim <file> --start <time> --end <time>`

## Presets

Default presets are in `flowdl/config/presets.json`:

- `music`: audio to MP3, high quality, `Downloads/Music`
- `video`: video, target resolution config, `Downloads/Videos`
- `podcast`: audio to MP3 with compression, `Downloads/Podcasts`

## Testing

```bash
python3 -m unittest discover -s tests -v
```

## Project Structure

```text
flowdl/
  cli/
  core/
  integrations/
  config/
  utils/
tests/
```

## Status

MVP complete. Planned future capabilities (not yet implemented) include channel watch mode and richer naming/metadata workflows.

## License

This project is licensed under the MIT License. See `LICENSE`.
