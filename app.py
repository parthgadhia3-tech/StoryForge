"""
StoryForge — a small platform for running a continuing AI story-video series.

v1 scope (this build): series/character setup, story-state continuity, and
LLM script generation per episode. Video generation is stubbed as the next
module to wire in (Wan 2.1 on a Colab GPU worker).
"""
import streamlit as st
import story_state as ss
import script_generator as sg

st.set_page_config(page_title="StoryForge", page_icon="🎬", layout="centered")

st.title("🎬 StoryForge")
st.caption("Your continuing AI story-video series — script + continuity engine")

# ---------------------------------------------------------------------------
# Sidebar: pick or create a series
# ---------------------------------------------------------------------------
st.sidebar.header("Series")

existing = ss.list_series()
options = ["+ Create new series"] + [s["title"] for s in existing]
choice = st.sidebar.selectbox("Choose a series", options)

if choice == "+ Create new series":
    st.sidebar.subheader("New series")
    new_title = st.sidebar.text_input("Series title", placeholder="e.g. The Last Signal")
    new_style = st.sidebar.text_input(
        "Art/tone style (used in every scene prompt)",
        placeholder="e.g. gritty neon-noir, handheld camera, moody lighting"
    )
    new_world = st.sidebar.text_area(
        "World / setting",
        placeholder="e.g. A near-future Mumbai where the power grid fails every night at 9pm."
    )
    st.sidebar.markdown("**Characters** (add at least one)")
    if "new_chars" not in st.session_state:
        st.session_state.new_chars = [{"name": "", "description": ""}]

    for i, c in enumerate(st.session_state.new_chars):
        c["name"] = st.sidebar.text_input(f"Character {i+1} name", value=c["name"], key=f"cname{i}")
        c["description"] = st.sidebar.text_area(
            f"Character {i+1} description (looks, personality, role)",
            value=c["description"], key=f"cdesc{i}"
        )

    col_a, col_b = st.sidebar.columns(2)
    if col_a.button("+ Add character"):
        st.session_state.new_chars.append({"name": "", "description": ""})
        st.rerun()

    if col_b.button("Create series", type="primary"):
        chars = [
            {"name": c["name"], "description": c["description"], "reference_image_url": ""}
            for c in st.session_state.new_chars if c["name"].strip()
        ]
        if not new_title.strip():
            st.sidebar.error("Give your series a title.")
        elif not chars:
            st.sidebar.error("Add at least one character.")
        else:
            slug = ss.create_series(new_title.strip(), new_style.strip(), new_world.strip(), chars)
            st.session_state.new_chars = [{"name": "", "description": ""}]
            st.sidebar.success(f"Created '{new_title}'!")
            st.session_state.active_slug = slug
            st.rerun()

    st.info("👈 Fill in the series details in the sidebar to get started.")
    st.stop()

else:
    active = next(s for s in existing if s["title"] == choice)
    slug = active["slug"]
    st.session_state.active_slug = slug

state = ss.load_state(slug)

# ---------------------------------------------------------------------------
# Main: series overview
# ---------------------------------------------------------------------------
st.header(state["series_title"])
with st.expander("Series bible (world, style, characters)", expanded=False):
    st.markdown(f"**Style:** {state.get('art_style') or '—'}")
    st.markdown(f"**World:** {state.get('world') or '—'}")
    st.markdown("**Characters:**")
    for c in state.get("characters", []):
        st.markdown(f"- **{c['name']}** — {c['description']}")

st.markdown(f"**Episodes so far:** {len(state['episodes'])}")
if state["episodes"]:
    last = state["episodes"][-1]
    st.markdown(f"**Last cliffhanger:** {last['cliffhanger']}")

st.divider()

# ---------------------------------------------------------------------------
# Generate next episode
# ---------------------------------------------------------------------------
st.subheader(f"Generate Episode {len(state['episodes']) + 1}")
episode_idea = st.text_area(
    "Optional: give this episode a specific idea/direction (leave blank to let it continue naturally)",
    placeholder="e.g. This episode, the protagonist discovers who's been sabotaging the grid."
)

if st.button("✨ Generate script", type="primary"):
    with st.spinner("Writing episode..."):
        try:
            result = sg.generate_episode(state, episode_idea)
            st.session_state.pending_episode = result
        except Exception as e:
            st.error(f"Script generation failed: {e}")

if "pending_episode" in st.session_state:
    ep = st.session_state.pending_episode
    st.success("Draft ready — review before saving to the series.")
    st.markdown("**Script:**")
    st.write(ep["script_text"])

    st.markdown("**Scenes:**")
    for sc in ep["scenes"]:
        st.markdown(f"- Scene {sc['scene_number']}: {sc['action']}" + (f" — *\"{sc['dialogue']}\"*" if sc.get("dialogue") else ""))

    st.markdown(f"**Summary (for continuity):** {ep['summary']}")
    st.markdown(f"**Cliffhanger:** {ep['cliffhanger']}")

    col1, col2 = st.columns(2)
    if col1.button("✅ Save episode to series"):
        ep_num = ss.add_episode(slug, ep["script_text"], ep["scenes"], ep["summary"], ep["cliffhanger"])
        del st.session_state.pending_episode
        st.success(f"Saved as Episode {ep_num}!")
        st.rerun()
    if col2.button("🔄 Discard and regenerate"):
        del st.session_state.pending_episode
        st.rerun()

    st.divider()
    st.subheader("🎥 Video generation")
    st.info(
        "Not wired up yet — this is the next module. Once saved, this episode's "
        "scenes are ready to hand off to the Wan 2.1 video-generation worker "
        "(run on a free Colab GPU) to produce the actual clips."
    )
