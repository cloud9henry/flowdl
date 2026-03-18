from flowdl.integrations.ytdlp_wrapper import download_with_ytdlp


def download_media(url: str, preset: dict) -> str:
    return download_with_ytdlp(url, preset)

