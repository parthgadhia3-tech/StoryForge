# StoryForge

A small platform for running a continuing AI story-video series: you set up a
series once (world, art style, characters), then generate each new episode's
script with one click — the app remembers everything that happened before and
writes each episode as a real continuation, not a fresh one-off.

**Current scope (v1):** series setup + story-continuity engine + script
generation. Video generation is intentionally stubbed — that's the next
module, which will call an open-source video model (Wan 2.1) running on a
free Colab GPU worker.

## How it works

- Each series is stored as a JSON file under `data/<series-slug>.json` —
  characters, world, art style, plot-so-far, and full episode history.
- Every time you generate a new episode, the app builds a prompt from that
  JSON (characters + plot-so-far + last cliffhanger + your optional idea for
  this episode) and asks the LLM to continue the story.
- When you save an episode, its summary and cliffhanger get appended back
  into the series file — so the next episode picks up correctly.

## Setup

1. Get a free Groq API key from https://console.groq.com/keys
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set your API key as an environment variable:
   ```
   export GROQ_API_KEY=your_key_here
   ```
4. Run locally:
   ```
   streamlit run app.py
   ```

## Deploying to Render (so it's reachable from your phone)

1. Push this folder to a GitHub repo (your fork).
2. On Render (render.com), create a new **Web Service** from that repo.
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add an environment variable: `GROQ_API_KEY` = your Groq key.
5. Deploy — Render gives you a public `https://yourapp.onrender.com` URL,
   reachable from your phone anywhere.

**Storage note:** Render's free tier filesystem is ephemeral — if the
service restarts, everything in `data/` is wiped. Fine for testing; before
relying on this daily, either upgrade to a paid disk, or swap `story_state.py`
to read/write to a free hosted store (e.g. a GitHub repo via API, or a small
free database) instead of local JSON files. Flagging this now so it isn't a
surprise later.

## Next steps (not built yet)

- Video generation module: take each saved episode's `scenes`, generate a
  character-consistent video clip per scene via Wan 2.1 (self-hosted on a
  free Colab GPU), then stitch with ffmpeg + TTS voiceover into the final
  video.
- Character reference images: one-time image generation per character,
  stored in `reference_image_url` on each character (currently empty),
  used to condition the video model for consistency.
