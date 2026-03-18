# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and this project follows Semantic Versioning where practical.

## [0.1.0] - 2026-03-18

### Added

- Initial FlowDL MVP CLI:
- `flowdl download <url> [--preset <name>]`
- `flowdl download <url> [--preset <name>] [--playlist]`
- `flowdl download <url> [--preset <name>] [--playlist] [--audio-sidecar]`
- `flowdl batch <file.txt> [--preset <name>] [--audio-sidecar]`
- `flowdl trim <file> --start <time> --end <time>`
- `flowdl clip <file> --timestamps <notes.txt>`
- `flowdl watch <url> [--preset <name>] [--once | --interval <minutes>]`
- `flowdl watch <url> [--preset <name>] [--once | --interval <minutes>] [--audio-sidecar]`
- Preset system with `music`, `video`, `podcast`, `mobile`, `lecture`
- Video downloads now prefer MP4 output via yt-dlp remux settings
- Preset-level filename templates for output naming (`filename_template`)
- Pipeline modules for download, post-process, and output organisation
- `yt-dlp` and `ffmpeg` integration wrappers
- Unit test suite with module-level coverage
