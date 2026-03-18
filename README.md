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

The default `lecture` preset also includes:
- `filename_template`: `{uploader} - {title}.{ext}`

## User Presets

User-level presets are supported at:

`~/.config/flowdl/presets.json`

FlowDL loads defaults first, then merges user presets on top (user keys override defaults).

### Filename Templates (Preset-level)

Set `filename_template` in a preset to control final output naming.

Supported keys:
- `{title}`
- `{uploader}`
- `{channel}`
- `{id}`
- `{upload_date}`
- `{preset}`
- `{ext}`

How it works:
- FlowDL extracts metadata from `yt-dlp` during download.
- The template is applied when moving processed output into the final preset folder.
- If a key is missing, FlowDL uses empty text (or source filename stem for title fallback).
- Illegal filename characters are sanitized automatically.
- If a file already exists, FlowDL appends a numeric suffix: `name.ext`, `name (1).ext`, `name (2).ext`.

Example user preset:

```json
{
  "lecture": {
    "filename_template": "{upload_date} - {uploader} - {title}.{ext}"
  }
}
```

Practical examples:
- `{uploader} - {title}.{ext}` -> `MIT OCW - Lecture 01.mp4`
- `{preset} - {title}.{ext}` -> `lecture - Linear Algebra Intro.mp4`
- `{upload_date} - {title}.{ext}` -> `20240201 - Week 3 Recap.mp4`

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

- Desktop GUI for non-CLI workflows
- Built-in transcription pipeline (`transcribe` command + timestamped artifacts)
- Metadata embedding and loudness normalization presets
- Download archive and retry/backoff policies
- Watch mode hardening (lockfile/single-instance guarantees)
- Packaged distribution (`pipx`, Homebrew tap)

## Contributing

Contributions are welcome. See `CONTRIBUTING.md`.

## License

MIT. See `LICENSE`.
