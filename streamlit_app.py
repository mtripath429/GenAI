# Ultra-Minimal Hangman (pure OpenAI, guaranteed ASCII gallows)
# Run: streamlit run streamlit_app.py
# Requires: pip install openai streamlit
# Needs: OPENAI_API_KEY in env or .streamlit/secrets.toml

import os
import re
import random
import streamlit as st
from openai import OpenAI

MAX_WRONG = 6

def get_client():
    key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not key:
        st.error("Missing OPENAI_API_KEY.")
        st.stop()
    return OpenAI(api_key=key)

@st.cache_data(show_spinner=False)
def pick_word(seed: int) -> str:
    """Ask the LLM for one lowercase a–z noun, 4–12 letters."""
    client = get_client()
    msgs = [
        {"role": "system", "content": "Return one lowercase English common noun (a–z only), 4–12 letters. Output only the word."},
        {"role": "user", "content": f"Seed: {seed}"}
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    w = resp.choices[0].message.content.strip().lower()
    w = re.sub(r"[^a-z]", "", w)
    if 4 <= len(w) <= 12:
        return w
    st.error("LLM returned an invalid word. Click New Game to try again.")
    st.stop()

def mask(secret: str, guessed: set) -> str:
    """Return the word pattern with underscores for unguessed letters."""
    return " ".join([c.upper() if c in guessed else "_" for c in secret])

def gallows(stage_wrong: int) -> str:
    """ASCII hangman based on number of wrong guesses (0..6)."""
    art = [
r"""  +---+
  |   |
      |
      |
      |
      |
=========""",
r"""  +---+
  |   |
  O   |
      |
      |
      |
=========""",
r"""  +---+
  |   |
  O   |
  |   |
      |
      |
=========""",
r"""  +---+
  |   |
  O   |
 /|   |
      |
      |
=========""",
r"""  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========""",
r"""  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========""",
r"""  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========""",
    ]
    stage_wrong = max(0, min(stage_wrong, MAX_WRONG))
    return art[stage_wrong]

@st.cache_data(show_spinner=False)
def render_panel(pattern: str, wrongs: list[str], remaining: int) -> str:
    """
    LLM renders a compact Markdown panel from visible state only.
    If the LLM omits the pattern, we prepend it ourselves (no hard fail).
    """
    wrong = ", ".join(wrongs) if wrongs else "none"
    client = get_client()
    msgs = [
        {"role": "system", "content": "Render a small Hangman panel in Markdown showing: the pattern prominently, wrong letters, guesses left, and a short line of encouragement. Do not reveal the word or any new letters."},
        {"role": "user", "content": f"Pattern: {pattern}\nWrong: {wrong}\nRemaining: {remaining}\nKeep it under ~60 words total."}
    ]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    md = resp.choices[0].message.content.strip()
    if pattern not in md:
        md = f"**{pattern}**\n\n" + md
    return md

def new_game():
    st.session_state.secret = pick_word(random.randint(1, 10**9))
    st.session_state.guessed = set()
    st.session_state.wrong = set()
    st.session_state.over = False

def guess(letter: str):
    if st.session_state.over or not letter or len(letter) != 1 or not letter.isalpha():
        return
    l = letter.lower()
    if l in st.session_state.guessed or l in st.session_state.wrong:
        return
    if l in st.session_state.secret:
        st.session_state.guessed.add(l)
        if all(c in st.session_state.guessed for c in st.session_state.secret):
            st.session_state.over = True
    else:
        st.session_state.wrong.add(l)
        if len(st.session_state.wrong) >= MAX_WRONG:
            st.session_state.over = True

# ---------- Streamlit ----------
st.set_page_config(page_title="Hangman (LLM)", layout="centered")
st.title("Hangman")

if "secret" not in st.session_state:
    new_game()

# New game button
if st.button("New Game"):
    new_game()
    st.rerun()

# Always show ASCII gallows (guaranteed)
wrong_count = len(st.session_state.wrong)
st.code(gallows(wrong_count), language=None)

# LLM-rendered panel
pattern = mask(st.session_state.secret, st.session_state.guessed)
remaining = MAX_WRONG - wrong_count
panel_md = render_panel(pattern, sorted(st.session_state.wrong), remaining)
st.markdown(panel_md)

# Single-letter input
letter = st.text_input("Your guess:", max_chars=1)
if letter:
    guess(letter)
    st.rerun()

# End-state message
if st.session_state.over:
    if wrong_count < MAX_WRONG:
        st.success("You solved it!")
    else:
        st.error(f"Out of guesses. The word was **{st.session_state.secret.upper()}**.")
