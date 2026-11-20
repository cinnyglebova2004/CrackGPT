import streamlit as st
import requests
import sqlite3
import base64
import uuid
from datetime import datetime
from PIL import Image
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="CrackGPT | Structural Intelligence", page_icon="🏗️", layout="wide")
DB_PATH = "crackgpt_chat_history.db"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """You are CrackGPT, a visual structural-damage discussion assistant.
Answer ONLY the user's current question. Do not automatically provide a full assessment or answer other questions that were not asked.
Use the uploaded image as evidence. Describe only details you can reasonably see. Clearly distinguish visible observations from possible explanations.
Do not invent material type, reinforcement exposure, corrosion, dimensions, severity, or structural safety. If something cannot be confirmed from the image, say so.
Keep answers concise, clear, and technically useful. For structural safety decisions, state that image-based assessment alone is not sufficient and an engineer/site inspection may be needed.
Maintain the conversation context so follow-up questions can refer to the same image and previous answers.
Only provide a complete structural damage assessment if the user explicitly asks for one.
"""

# ---------------- DATABASE ----------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT, image BLOB, image_type TEXT, created TEXT, updated TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id TEXT, role TEXT, content TEXT, created TEXT)")
    conn.commit()
    return conn


def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    conn = db()
    conn.execute("INSERT INTO chats (id,title,image,image_type,created,updated) VALUES (?,?,?,?,?,?)", (chat_id, "New conversation", None, None, now, now))
    conn.commit()
    conn.close()
    return chat_id


def get_chats():
    conn = db()
    rows = conn.execute("SELECT id,title,updated FROM chats ORDER BY updated DESC").fetchall()
    conn.close()
    return rows


def get_chat(chat_id):
    conn = db()
    row = conn.execute("SELECT id,title,image,image_type FROM chats WHERE id=?", (chat_id,)).fetchone()
    conn.close()
    return row


def save_image(chat_id, image_bytes, image_type):
    conn = db()
    conn.execute("UPDATE chats SET image=?, image_type=?, updated=? WHERE id=?", (image_bytes, image_type, datetime.now().isoformat(timespec="seconds"), chat_id))
    conn.commit()
    conn.close()


def save_message(chat_id, role, content):
    conn = db()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("INSERT INTO messages (chat_id,role,content,created) VALUES (?,?,?,?)", (chat_id, role, content, now))
    conn.execute("UPDATE chats SET updated=? WHERE id=?", (now, chat_id))
    conn.commit()
    conn.close()


def get_messages(chat_id):
    conn = db()
    rows = conn.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()
    conn.close()
    return rows


def update_title(chat_id, title):
    conn = db()
    conn.execute("UPDATE chats SET title=? WHERE id=? AND title='New conversation'", (title[:55], chat_id))
    conn.commit()
    conn.close()

# ---------------- HELPERS ----------------
def image_data_url(image_bytes, image_type):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{image_type};base64,{encoded}"



def ask_groq(chat_id, question, image_bytes, image_type, history):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    model = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)
