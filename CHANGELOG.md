# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog and this project follows Semantic Versioning where practical.

## [0.1.0] - 2026-03-18

### Added

- Initial FlowDL MVP CLI:
- `flowdl download <url> [--preset <name>]`
- `flowdl download <url> [--preset <name>] [--playlist]`
- `flowdl batch <file.txt> [--preset <name>]`
- `flowdl trim <file> --start <time> --end <time>`
- Preset system with `music`, `video`, `podcast`
- Pipeline modules for download, post-process, and output organisation
- `yt-dlp` and `ffmpeg` integration wrappers
- Unit test suite with module-level coverage
