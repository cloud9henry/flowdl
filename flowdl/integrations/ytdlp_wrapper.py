from pathlib import Path
from urllib.parse import urlparse

from flowdl.core.models import DownloadedMedia
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


def download_with_ytdlp(url: str, preset: dict, temp_dir: str = "temp") -> DownloadedMedia:
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
    if preset.get("mode") == "video":
        # Prefer broadly compatible MP4 outputs for video workflows.
        ydl_opts["merge_output_format"] = "mp4"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }
        ]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            output_path = ydl.prepare_filename(info)
            metadata = {
                "title": str(info.get("title") or ""),
                "uploader": str(info.get("uploader") or ""),
                "channel": str(info.get("channel") or ""),
                "id": str(info.get("id") or ""),
                "upload_date": str(info.get("upload_date") or ""),
            }
            return DownloadedMedia(file_path=str(Path(output_path)), metadata=metadata)
    except DownloadError as exc:
        raise RuntimeError(f"Download failed for URL '{url}': {exc}") from exc


def list_playlist_urls(url: str) -> list[str]:
    if not _is_likely_url(url):
        raise InvalidURLError(f"Invalid URL: {url}")

    if YoutubeDL is None:
        raise RuntimeError("yt-dlp is not installed. Install dependencies first.")

    ydl_opts = {
        "extract_flat": True,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") != "playlist":
        return [url]

    output_urls: list[str] = []
    for entry in info.get("entries", []):
        if not entry:
            continue

        webpage_url = entry.get("webpage_url")
        if webpage_url:
            output_urls.append(webpage_url)
            continue

        candidate_url = entry.get("url")
        if candidate_url and str(candidate_url).startswith(("http://", "https://")):
            output_urls.append(str(candidate_url))
            continue

        video_id = entry.get("id") or candidate_url
        if video_id:
            output_urls.append(f"https://www.youtube.com/watch?v={video_id}")

    return output_urls
