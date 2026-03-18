from flowdl.core.downloader import download_media
from flowdl.core.organiser import organise_output
from flowdl.core.processor import postprocess


def run_pipeline(url: str, preset: dict) -> str:
    file_path = download_media(url, preset)
    processed_file = postprocess(file_path, preset)
    final_path = organise_output(processed_file, preset)
    return final_path

