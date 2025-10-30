# Ultra-Minimal Hangman (pure OpenAI version, fixed rerun)
# Run: streamlit run streamlit_app.py
# Requires: pip install openai streamlit

import os, re, random, streamlit as st
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
    client = get_client()
    msg = [
        {"role": "system", "content": "Return one lowercase English noun (4–12 letters, a–z only)."},
        {"role": "user", "content": f"Seed: {seed}"}
    ]
    r = client.chat.completions.create(model="gpt-4o-mini", messages=msg)
    w = r.choices[0].message.content.strip().lower()
    w = re.sub(r"[^a-z]","",w)
    return w if 4 <= len(w) <= 12 else "hangman"

def mask(secret, guessed):
    return " ".join([c.upper() if c in guessed else "_" for c in secret])

@st.cache_data(show_spinner=False)
def render_panel(pattern, wrongs, remaining):
    wrong = ", ".join(wrongs) if wrongs else "none"
    client = get_client()
    msg = [
        {"role": "system", "content": "Render a small Hangman board in Markdown showing pattern, wrong letters, guesses left, and a short line of encouragement."},
        {"role": "user", "content": f"Pattern: {pattern}\nWrong: {wrong}\nRemaining: {remaining}"}
    ]
    r = client.chat.completions.create(model="gpt-4o-mini", messages=msg)
    return r.choices[0].message.content.strip()

def new_game():
    st.session_state.secret = pick_word(random.randint(1,1e9))
    st.session_state.guessed, st.session_state.wrong = set(), set()
    st.session_state.over = False

def guess(l):
    if st.session_state.over or not l.isalpha() or len(l)!=1: return
    l = l.lower()
    if l in st.session_state.guessed or l in st.session_state.wrong: return
    if l in st.session_state.secret:
        st.session_state.guessed.add(l)
        if all(c in st.session_state.guessed for c in st.session_state.secret):
            st.session_state.over=True
    else:
        st.session_state.wrong.add(l)
        if len(st.session_state.wrong)>=MAX_WRONG: st.session_state.over=True

# ---------- Streamlit ----------
st.set_page_config(page_title="Hangman (LLM)", layout="centered")
st.title("Hangman")

if "secret" not in st.session_state:
    new_game()

if st.button("New Game"):
    new_game()
    st.experimental_rerun()

pattern = mask(st.session_state.secret, st.session_state.guessed)
remaining = MAX_WRONG - len(st.session_state.wrong)
st.markdown(render_panel(pattern, sorted(st.session_state.wrong), remaining))

letter = st.text_input("Your guess:", max_chars=1)
if letter:
    guess(letter)
    st.experimental_rerun()

if st.session_state.over:
    if len(st.session_state.wrong) < MAX_WRONG:
        st.success("You solved it!")
    else:
        st.error(f"Out of guesses. The word was **{st.session_state.secret.upper()}**.")
