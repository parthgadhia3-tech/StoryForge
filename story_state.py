"""
story_state.py
Handles persistent story continuity: characters, world, plot-so-far, episode history.
Each series gets its own JSON file under data/<series_slug>.json
"""
import json
import os
import re
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except FileExistsError:
    pass



def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled-series"


def series_path(slug: str) -> str:
    return os.path.join(DATA_DIR, f"{slug}.json")


def list_series():
    """Return a list of {slug, title} for every existing series."""
    out = []
    if not os.path.exists(DATA_DIR):
        return out
    for fname in sorted(os.listdir(DATA_DIR)):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, fname), "r", encoding="utf-8") as f:
                    data = json.load(f)
                out.append({"slug": fname[:-5], "title": data.get("series_title", fname[:-5])})
            except Exception:
                continue
    return out


def create_series(title: str, art_style: str, world: str, characters: list) -> str:
    """Create a new series file. characters is a list of dicts:
    {"name": ..., "description": ..., "reference_image_url": ""}
    Returns the slug.
    """
    slug = slugify(title)
    path = series_path(slug)
    if os.path.exists(path):
        raise ValueError(f"A series with slug '{slug}' already exists.")

    state = {
        "series_title": title,
        "art_style": art_style,
        "world": world,
        "characters": characters,
        "plot_so_far": "",
        "episodes": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(slug, state)
    return slug


def load_state(slug: str) -> dict:
    path = series_path(slug)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No series found for slug '{slug}'")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(slug: str, state: dict):
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = series_path(slug)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def add_episode(slug: str, script: str, scenes: list, summary: str, cliffhanger: str):
    """Append a completed episode to the series history and roll the plot forward."""
    state = load_state(slug)
    ep_number = len(state["episodes"]) + 1
    state["episodes"].append({
        "ep_number": ep_number,
        "script": script,
        "scenes": scenes,
        "summary": summary,
        "cliffhanger": cliffhanger,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    # Roll plot_so_far forward so future episodes stay in continuity
    prior = state.get("plot_so_far", "")
    state["plot_so_far"] = (prior + f"\n\nEpisode {ep_number}: {summary}").strip()
    save_state(slug, state)
    return ep_number


def last_cliffhanger(slug: str) -> str:
    state = load_state(slug)
    if state["episodes"]:
        return state["episodes"][-1].get("cliffhanger", "")
    return ""
