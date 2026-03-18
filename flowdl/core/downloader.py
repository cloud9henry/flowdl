from flowdl.integrations.ytdlp_wrapper import download_with_ytdlp, list_playlist_urls


def download_media(url: str, preset: dict) -> str:
    return download_with_ytdlp(url, preset)


def get_playlist_urls(url: str) -> list[str]:
    return list_playlist_urls(url)
