import os
import time
import base64
import streamlit as st
from google import genai

# ---------- Page setup ----------
st.set_page_config(page_title="DigiVam | Vamsi's AI", page_icon="🤖", layout="centered", initial_sidebar_state="auto")

# ---------- Your images (put these files in the same folder as app.py) ----------
ROBOT_IMG = "robo1.jpg"          # used in the header circle and the chat bot avatar
PHOTO_URL = "roboai.jpeg"          # big circle in the left panel (file name OR https link)


def img_uri(path):
    """Turn a local image file into a data link the page can show. Returns None if not found."""
    if path and os.path.exists(path):
        ext = path.rsplit(".", 1)[-1].lower()
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        with open(path, "rb") as f:
            return f"data:image/{mime};base64,{base64.b64encode(f.read()).decode()}"
    return None


def circle_img_html(src, css_class, fallback_letter="V"):
    src = (src or "").strip()
    if src.startswith("http"):
        return f'<img class="{css_class}" src="{src}">'
    uri = img_uri(src)
    if uri:
        return f'<img class="{css_class}" src="{uri}">'
    return f'<div class="{css_class} placeholder">{fallback_letter}</div>'


BOT_AVATAR = ROBOT_IMG if os.path.exists(ROBOT_IMG) else "🤖"
USER_AVATAR = "🤵🏻"

# ---------- Modern styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }

/* Background */
.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(37,99,205,0.22), transparent 20%),
        radial-gradient(circle at 85% 20%, rgba(37,99,205,0.22), transparent 20%),
        #000000;
}

/* Hide default Streamlit clutter */
#MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 2rem; padding-bottom: 7rem; background:#000; }

/* Hero card */
.hero {
    display: flex; align-items: center; gap: 16px;
    padding: 20px 22px; margin-bottom: 14px;
    background: #000;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 20px;
    backdrop-filter: blur(14px);
}
.avatar {
    width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0;
    overflow: hidden;
    border: 2px solid rgba(255,255,255,0.85);
    box-shadow: 0 0 24px rgba(37,99,235,0.55);
}
.avatar img { width: 100%; height: 100%; object-fit: cover; display: block; }
.avatar.placeholder {
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; font-weight: 700; color: #fff;
    background: linear-gradient(135deg, #2563eb, #38bdf8);
}
.name { font-size: 24px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 10px; }
.tag { font-size: 14px; color: #9ca3af; margin-top: 2px; }
.badge {
    font-size: 11px; font-weight: 600; color: #34d399;
    background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
    padding: 2px 9px; border-radius: 999px; display: inline-flex; align-items: center; gap: 5px;
}
.dot { width: 6px; height: 6px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399; }

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px; padding: 14px 18px; margin-bottom: 12px;
    color: #e5e7eb;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse; text-align: right;
    background: linear-gradient(135deg, rgba(37,99,235,0.85), rgba(56,189,248,0.75));
    border: none; color: #fff;
}
/* Round chat avatars with images */
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarUser"] { border-radius: 50%; overflow: hidden; }
[data-testid="stChatMessageAvatarAssistant"] img,
[data-testid="stChatMessageAvatarUser"] img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }

/* Suggestion buttons */
div.stButton > button {
    width: 100%; border-radius: 14px; padding: 12px 14px;
    background: rgba(255,255,255,0.05); color: #e5e7eb;
    border: 1px solid rgba(255,255,255,0.12);
    transition: all .2s ease;
}
div.stButton > button:hover {
    border-color: #60a5fa; color: #fff;
    background: rgba(37,99,235,0.18); transform: translateY(-2px);
}

/* Chat input */
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stChatInput"] {
    border-radius: 18px; background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.14);
}
[data-testid="stChatInput"]:focus-within { border-color: #60a5fa; box-shadow: 0 0 0 3px rgba(96,165,250,0.2); }

/* Left profile panel */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03);
    border-right: 1px solid rgba(255,255,255,0.08);
}
.side { text-align: center; padding-top: 8px; }
.photo {
    display: block; margin: 0 auto 16px auto;
    width: 170px; height: 170px; border-radius: 50%; object-fit: cover;
    border: 3px solid rgba(255,255,255,0.85);
}
.photo.placeholder {
    display: flex; align-items: center; justify-content: center;
    font-size: 64px; font-weight: 700; color: #fff;
    background: linear-gradient(135deg, #2563eb, #38bdf8);
}
.side h3 { color: #fff; font-size: 20px; font-weight: 700; margin: 0; }
.side p { color: #9ca3af; font-size: 13px; margin: 4px 0 14px 0; }
.side a.btn {
    display: block; margin: 8px 0; padding: 9px 12px; border-radius: 12px;
    font-size: 13px; font-weight: 500; text-decoration: none; color: #e5e7eb;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
}
.side a.btn:hover { border-color: #60a5fa; background: rgba(37,99,235,0.18); }
@media (max-width: 768px) {
    [data-testid="stSidebar"] {
        background: #0b0b0f !important;   /* solid so chat doesn't show through */
    }
    .photo { width: 120px; height: 120px; }  /* optional: smaller photo on phones */
}
.mobile-link { display: none; }

@media (max-width: 768px) {
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"],
    [data-testid="stExpandSidebarButton"] { display: none !important; }

    .mobile-link {
        display: inline-block; margin-top: 8px; padding: 5px 12px;
        font-size: 12px; color: #fff; text-decoration: none;
        border: 1px solid rgba(255,255,255,0.25); border-radius: 999px;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------- Hero header (image inside the circle) ----------
_uri = img_uri(ROBOT_IMG)
_avatar = f'<div class="avatar"><img src="{_uri}"></div>' if _uri else '<div class="avatar placeholder">V</div>'

st.markdown(f"""
<div class="hero">
{_avatar}
<div>
<div class="name">DigiVam <span class="badge"><span class="dot"></span>Online</span></div>
<div class="tag">Vamsi's AI twin. Ask about his skills, projects and education.</div>
</div>
</div>
""", unsafe_allow_html=True)

# ---------- Left side profile photo ----------
with st.sidebar:
    st.markdown(f"""
<div class="side">
{circle_img_html(PHOTO_URL, "photo")}
<h3> Vamsi Madhukar</h3>
<p>Aspiring software developer</p>
<a class="btn" href="https://vamsimadhukar01-cmd.github.io/vamsimadhukar.github.io/" target="_blank">🌐 View Portfolio</a>
</div>
""", unsafe_allow_html=True)

# ---------- Load key and about-me data ----------
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

with open("aboutme.txt", encoding="utf-8") as f:
    about_me = f.read()

system_prompt = f"""You are DigiVam, an AI that answers questions about Vamsi.
Use ONLY the information below. If the answer isn't there,
say "I don't have that info, please contact Vamsi directly."
Be friendly and professional.

{about_me}"""

MODELS = ["gemini-3.5-flash", "gemini-2.5-flash"]


# ---------- Ask the AI (with retry if busy) ----------
def ask_ai(history):
    # skip the first message (the greeting), Gemini expects the chat to start with the user
    contents = [
        {"role": "user" if m["role"] == "user" else "model",
         "parts": [{"text": m["content"]}]}
        for m in history[1:]
    ]
    for attempt in range(3):
        for model in MODELS:
            try:
                reply = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config={"system_instruction": system_prompt},
                )
                return reply.text
            except Exception as e:
                print(f"[{model}] error: {e}")  # shows the real error in your terminal
                continue
        time.sleep(3)
    return "Sorry, the AI is busy right now. Please try again in a minute."


# ---------- Chat memory ----------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Hi! I'm DigiVam, Vamsi's AI. Ask me anything about him."}
    ]

# ---------- Suggested questions (only at the start) ----------
pending = st.session_state.pop("pending", None)
if len(st.session_state.messages) == 1 and not pending:
    st.caption("Try asking:")
    suggestions = [
        "Tell me about his projects",
        "What internships has he done?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"sug{i}"):
            st.session_state.pending = s
            st.rerun()

# ---------- Show chat history ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar=USER_AVATAR if m["role"] == "user" else BOT_AVATAR):
        st.write(m["content"])

# ---------- Handle new question ----------
question = st.chat_input("Ask about Vamsi...") or pending
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.write(question)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Computing..."):
            answer = ask_ai(st.session_state.messages)
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})