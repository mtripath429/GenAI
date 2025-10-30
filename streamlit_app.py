
import os, re, random, streamlit as st
from langchain_openai import ChatOpenAI

MAX_WRONG = 6

def llm(temp=0.6):
    key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
    if not key:
        st.error("Missing OPENAI_API_KEY.")
        st.stop()
    return ChatOpenAI(model="gpt-4o-mini", temperature=temp, openai_api_key=key)

@st.cache_data(show_spinner=False)
def pick_word(seed: int) -> str:
    msg = [
        ("system","Output one lowercase English noun (a–z only, 4–12 letters). Nothing else."),
        ("user",f"Seed: {seed}")
    ]
    w = llm(0.7).invoke(msg).content.strip().lower()
    w = re.sub(r"[^a-z]","",w)
    return w if 4 <= len(w) <= 12 else "hangman"

def mask(secret, guessed): 
    return " ".join([c.upper() if c in guessed else "_" for c in secret])

@st.cache_data(show_spinner=False)
def render_panel(pattern, wrongs, remaining):
    wrong = ", ".join(wrongs) if wrongs else "none"
    msg = [
        ("system","Render a small Hangman board in Markdown with pattern, wrong letters, guesses left, and a short line of encouragement."),
        ("user",f"Pattern: {pattern}\nWrong: {wrong}\nRemaining: {remaining}")
    ]
    return llm(0.5).invoke(msg).content.strip()

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
        if len(st.session_state.wrong)>=MAX_WRONG:
            st.session_state.over=True

# ---------- Streamlit ----------
st.set_page_config(page_title="Hangman (LLM)", layout="centered")
st.title("Hangman")

if "secret" not in st.session_state: new_game()

if st.button("New Game"): new_game(); st.experimental_rerun()

pattern = mask(st.session_state.secret, st.session_state.guessed)
remaining = MAX_WRONG - len(st.session_state.wrong)
st.markdown(render_panel(pattern, sorted(st.session_state.wrong), remaining))

letter = st.text_input("Your guess:", max_chars=1)
if letter: guess(letter); st.experimental_rerun()

if st.session_state.over:
    if len(st.session_state.wrong) < MAX_WRONG:
        st.success("You solved it!")
    else:
        st.error(f"Out of guesses. The word was **{st.session_state.secret.upper()}**.")
