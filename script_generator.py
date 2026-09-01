"""
script_generator.py
Generates a new episode's script using an LLM, grounded in the series' story_state
so it continues the plot instead of starting fresh each time.

Uses Groq's OpenAI-compatible API by default. Swap BASE_URL/MODEL for another
provider later without touching the rest of the app.
"""
import os
import json
from openai import OpenAI

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

SCRIPT_SYSTEM_PROMPT = """You are a professional serial drama writer. You write tight, \
visual, scene-by-scene scripts for short-form vertical video (45-75 seconds spoken). \
You always continue the ongoing story faithfully — respect established characters, \
world rules, and the plot-so-far. Each episode should end on a hook/cliffhanger that \
pulls the viewer into the next episode.

Return ONLY valid JSON, no markdown fences, no commentary, in this exact shape:
{
  "script_text": "the full narration/dialogue as one readable script",
  "scenes": [
    {"scene_number": 1, "action": "what happens, for a video prompt", "dialogue": "spoken line, if any"}
  ],
  "summary": "1-2 sentence summary of what happened this episode, for continuity",
  "cliffhanger": "1 sentence describing how this episode ends / what's unresolved"
}
"""


def _client() -> OpenAI:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "No LLM API key set. Set the GROQ_API_KEY environment variable "
            "(or point LLM_BASE_URL/LLM_MODEL at another OpenAI-compatible provider)."
        )
    return OpenAI(api_key=GROQ_API_KEY, base_url=BASE_URL)


def build_user_prompt(state: dict, episode_idea: str = "") -> str:
    characters = "\n".join(
        f"- {c['name']}: {c['description']}" for c in state.get("characters", [])
    )
    ep_number = len(state.get("episodes", [])) + 1
    prior_cliff = state["episodes"][-1]["cliffhanger"] if state.get("episodes") else "This is episode 1 — no prior cliffhanger."

    idea_block = f"\nSpecific idea for this episode (follow this if given): {episode_idea}\n" if episode_idea else ""

    return f"""Series: {state.get('series_title')}
Art/tone style: {state.get('art_style')}
World: {state.get('world')}

Characters:
{characters}

Plot so far:
{state.get('plot_so_far') or '(Nothing yet — this is the first episode.)'}

Last episode's cliffhanger to pick up from:
{prior_cliff}
{idea_block}
Write episode {ep_number} now. Keep it tight for a ~60 second vertical video, 4-7 scenes.
"""


def generate_episode(state: dict, episode_idea: str = "") -> dict:
    """Calls the LLM and returns a dict: script_text, scenes, summary, cliffhanger."""
    client = _client()
    user_prompt = build_user_prompt(state, episode_idea)

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.9,
        max_tokens=1500,
    )
    raw = resp.choices[0].message.content.strip()

    # Defensive cleanup in case the model wraps in markdown fences anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM did not return valid JSON. Raw response:\n{raw}") from e

    for key in ("script_text", "scenes", "summary", "cliffhanger"):
        if key not in data:
            raise RuntimeError(f"LLM response missing required field '{key}'. Got: {data}")

    return data
