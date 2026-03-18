import json
import time
from pathlib import Path

from flowdl.core.downloader import get_playlist_urls
from flowdl.core.pipeline import run_pipeline


def _default_state_path() -> Path:
    return Path.home() / ".flowdl" / "watch_state.json"


def load_watch_state(state_path: str | Path | None = None) -> dict:
    path = Path(state_path) if state_path else _default_state_path()
    if not path.exists():
        return {"sources": {}}

    data = json.loads(path.read_text(encoding="utf-8"))
    if "sources" not in data or not isinstance(data["sources"], dict):
        return {"sources": {}}
    return data


def save_watch_state(state: dict, state_path: str | Path | None = None) -> None:
    path = Path(state_path) if state_path else _default_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def watch_once(source_url: str, preset: dict, state_path: str | Path | None = None) -> dict:
    state = load_watch_state(state_path)
    sources = state.setdefault("sources", {})
    source_state = sources.setdefault(source_url, {"seen_urls": []})
    seen_urls = set(source_state.get("seen_urls", []))

    discovered_urls = get_playlist_urls(source_url)
    new_urls = [url for url in discovered_urls if url not in seen_urls]

    processed = 0
    failed = 0
    for url in new_urls:
        try:
            run_pipeline(url, preset)
            seen_urls.add(url)
            processed += 1
        except Exception:
            failed += 1

    source_state["seen_urls"] = sorted(seen_urls)
    save_watch_state(state, state_path)

    return {
        "discovered": len(discovered_urls),
        "new": len(new_urls),
        "processed": processed,
        "failed": failed,
    }


def watch_interval(source_url: str, preset: dict, interval_minutes: int, state_path: str | Path | None = None) -> None:
    if interval_minutes <= 0:
        raise ValueError("interval_minutes must be greater than 0")

    while True:
        watch_once(source_url, preset, state_path=state_path)
        time.sleep(interval_minutes * 60)

