from pathlib import Path
from urllib.parse import urlparse

from flowdl.utils.errors import InvalidURLError

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError
except ImportError:  # pragma: no cover
    YoutubeDL = None
    DownloadError = Exception


def _is_likely_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def download_with_ytdlp(url: str, preset: dict, temp_dir: str = "temp") -> str:
    if not _is_likely_url(url):
        raise InvalidURLError(f"Invalid URL: {url}")

    if YoutubeDL is None:
        raise RuntimeError("yt-dlp is not installed. Install dependencies first.")

    format_selector = "bestaudio/best" if preset.get("mode") == "audio" else "bestvideo+bestaudio/best"

    temp_path = Path(temp_dir).expanduser()
    temp_path.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": format_selector,
        "outtmpl": str(temp_path / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output_path = ydl.prepare_filename(info)
            return str(Path(output_path))
    except DownloadError as exc:
        raise RuntimeError(f"Download failed for URL '{url}': {exc}") from exc

