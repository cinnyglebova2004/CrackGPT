import streamlit as st
import requests, base64, sqlite3, uuid, os, json
from datetime import datetime
from io import BytesIO
from PIL import Image

# ===================== CONFIG =====================
DB_PATH = "crackgpt_chat_history.db"
GROQ_MODEL = "qwen/qwen3.8-27b"  # multimodal vision model
API_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = """You are CrackGPT, a focused conversational assistant for preliminary visual structural damage assessment.

STRICT CONVERSATION RULES:
- Answer ONLY the exact question in the latest user message. Do not answer any other assessment questions unless the user asks them.
- Do not volunteer a full assessment, extra headings, causes, risks, tests, or repairs when they were not requested.
- Keep answers concise: normally 2-5 sentences, or a few short bullets only if the current question needs them.
- The uploaded image is the visual evidence. Use previous messages only as conversation context, not as a reason to repeat them.
- Stay consistent about the material and damage visible in the image. Never switch from concrete to wood (or another material) without clear visual evidence.
- Do not hallucinate. If a feature is unclear or not visible, say so plainly.
- Distinguish visible observations from interpretations. Rust staining alone does not prove exposed reinforcement or active corrosion.
- Do not diagnose severity as certain from an image alone and never declare the structure safe or unsafe.
- For the user's current question: damage type -> name the visible type only; location -> location only; appearance -> describe only; severity -> severity and visible reasons; causes -> plausible causes only; risks -> risks only; durability -> durability only; tests -> tests only; repair -> repair methods only.
- Give a complete assessment with sections ONLY when the user explicitly asks for a complete/overall assessment or summary.
- If the user asks a follow-up, directly address it without restarting the assessment.
- Use plain, professional, engineering language. No filler greetings, apologies, or closing offers.
- Remind the user that visual assessment is preliminary and requires on-site inspection only when safety, severity, or repair decisions are discussed, and keep that reminder brief.
"""

st.set_page_config(page_title="CrackGPT | Structural Intelligence", page_icon="🏗️", layout="wide")
st.markdown("""<style>
.stApp{background:#101114;color:#f3f3f3} section[data-testid='stSidebar']{background:#191a20}
[data-testid='stChatMessage']{border-radius:14px} div[data-testid='stChatInput']{background:#24252b}
</style>""", unsafe_allow_html=True)


# ===================== SQLITE =====================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT, created_at TEXT, image_name TEXT, image_data BLOB, image_mime TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT, created_at TEXT)")
    conn.commit()
    return conn

conn = db()


def new_chat():
    chat_id = str(uuid.uuid4())
    conn.execute("INSERT INTO chats (id,title,created_at,image_name,image_data,image_mime) VALUES (?,?,?,?,?,?)", (chat_id, "New conversation", datetime.now().isoformat(), None, None, None))
    conn.commit()
    st.query_params["chat"] = chat_id
    return chat_id


def get_chat(chat_id):
    return conn.execute("SELECT id,title,image_name,image_data,image_mime FROM chats WHERE id=?", (chat_id,)).fetchone()


def get_messages(chat_id):
    rows = conn.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]


def save_message(chat_id, role, content):
    conn.execute("INSERT INTO messages(chat_id,role,content,created_at) VALUES(?,?,?,?)", (chat_id, role, content, datetime.now().isoformat()))
    conn.commit()


def update_title(chat_id, title):
    conn.execute("UPDATE chats SET title=? WHERE id=? AND title='New conversation'", (title[:70], chat_id))
    conn.commit()


def save_image(chat_id, file):
    raw = file.getvalue()
    mime = file.type or "image/jpeg"
    conn.execute("UPDATE chats SET image_name=?, image_data=?, image_mime=? WHERE id=?", (file.name, raw, mime, chat_id))
    conn.commit()

# ===================== CHAT ID =====================
chat_id = st.query_params.get("chat")
if not chat_id or not get_chat(chat_id):
    chat_id = new_chat()
chat = get_chat(chat_id)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("# 🏗️ CrackGPT")
    st.caption("Structural Intelligence")
    if st.button("＋ New conversation", use_container_width=True):
        new_chat()
        st.rerun()
    st.divider()
    st.markdown("### CrackGPT Vision")
    st.caption("Image-based structural damage discussion")
    st.caption("Conversational question-by-question assessment")
