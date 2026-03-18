from dataclasses import dataclass


@dataclass
class DownloadedMedia:
    file_path: str
    metadata: dict[str, str]

