import streamlit as st
import requests
import base64
import sqlite3
import uuid
from datetime import datetime
from io import BytesIO
from PIL import Image

# ================= CONFIG =================
DB_PATH = "crackgpt_chat_history.db"
GROQ_MODEL = "qwen/qwen3.8-27b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """
You are CrackGPT, an AI assistant for preliminary structural damage assessment.

Answer ONLY the user's current question.
Maintain context from previous messages and the uploaded image.

Your expertise includes:
- Cracking
- Spalling
- Corrosion
- Honeycombing
- Voids
- Exposed reinforcement
- Delamination
- Concrete deterioration
- Structural durability
- Inspection and rehabilitation

RULES:
1. Answer the exact question asked.
2. Give complete, useful engineering explanations.
3. Do not automatically answer all assessment questions.
4. Maintain a natural conversation.
5. Remember the previous conversation.
6. Do not repeat the same answer unnecessarily.
7. Separate visible observations from assumptions.
8. Never claim reinforcement is exposed unless visually supported.
9. Never confirm corrosion solely from discoloration.
10. Do not invent damage.
11. Explain uncertainty honestly.
12. Do not declare a structure safe or unsafe from an image alone.
13. For severity questions, explain the evidence and limitations.
14. For causes, explain plausible causes without claiming certainty.
15. For repair questions, recommend appropriate engineering procedures.
16. Use clear, professional but understandable language.

If the user asks for a complete assessment, use:
- Observed damage
- Location
- Severity
- Possible causes
- Structural risks
- Recommended inspection
- Repair recommendations

Assessments are preliminary visual assessments and must not replace
an on-site inspection by a qualified structural engineer.
"""

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #101114;
    color: #f3f3f3;
}
section[data-testid="stSidebar"] {
    background-color: #191a20;
}
[data-testid="stChatMessage"] {
    border-radius: 14px;
}
div[data-testid="stChatInput"] {
    background-color: #24252b;
}
</style>
""", unsafe_allow_html=True)


# ================= DATABASE =================
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            image_name TEXT,
            image_data BLOB,
            image_mime TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    return conn


conn = db()


# ================= CHAT FUNCTIONS =================
def new_chat():
    chat_id = str(uuid.uuid4())

    conn.execute(
        """INSERT INTO chats
        (id,title,created_at,image_name,image_data,image_mime)
        VALUES (?,?,?,?,?,?)""",
        (
            chat_id,
            "New conversation",
            datetime.now().isoformat(),
            None,
            None,
            None
        )
    )

    conn.commit()
    st.query_params["chat"] = chat_id
    return chat_id


def get_chat(chat_id):
    return conn.execute(
        """SELECT id,title,image_name,image_data,image_mime
        FROM chats WHERE id=?""",
        (chat_id,)
    ).fetchone()


def get_messages(chat_id):
    rows = conn.execute(
        """SELECT role,content FROM messages
        WHERE chat_id=? ORDER BY id""",
        (chat_id,)
    ).fetchall()

    return [
        {"role": row[0], "content": row[1]}
        for row in rows
    ]


def save_message(chat_id, role, content):
    conn.execute(
        """INSERT INTO messages
        (chat_id,role,content,created_at)
        VALUES (?,?,?,?)""",
        (
            chat_id,
            role,
            content,
            datetime.now().isoformat()
        )
    )
    conn.commit()


def update_title(chat_id, title):
    conn.execute(
        """UPDATE chats SET title=?
        WHERE id=? AND title='New conversation'""",
        (title[:70], chat_id)
    )
    conn.commit()


def save_image(chat_id, file):
    raw = file.getvalue()
    mime = file.type or "image/jpeg"

    conn.execute(
        """UPDATE chats
        SET image_name=?,image_data=?,image_mime=?
        WHERE id=?""",
        (file.name, raw, mime, chat_id)
    )
    conn.commit()


# ================= CURRENT CHAT =================
chat_id = st.query_params.get("chat")

if not chat_id or not get_chat(chat_id):
    chat_id = new_chat()

chat = get_chat(chat_id)


# ================= SIDEBAR =================
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

    st.divider()

    st.markdown("### Damage Topics")
    st.caption(
        "Cracking · Spalling · Corrosion · Honeycombing · "
        "Voids · Delamination"
    )

    st.divider()
    st.caption("Preliminary visual assessment")


# ================= MAIN PAGE =================
st.title("🏗️ CrackGPT Structural Assessment")

st.caption(
    "Upload an image once and ask questions one at a time. "
    "Your conversation is saved in this chat."
)


# ================= IMAGE UPLOAD =================
image_name = chat[2]
image_blob = chat[3]
image_mime = chat[4]

upload = st.file_uploader(
    "Upload a structural damage image",
    type=["jpg", "jpeg", "png", "webp"]
)

if upload is not None:

    if upload.name != image_name:
        save_image(chat_id, upload)
        st.rerun()


# ================= DISPLAY IMAGE =================
if image_blob:

    try:
        image = Image.open(
            BytesIO(image_blob)
        ).convert("RGB")

        st.image(
            image,
            caption="Image attached to this conversation",
            width=560
        )

    except Exception:
        image = None

else:

    image = None
    st.info("Upload an image to begin.")


# ================= CHAT HISTORY =================
messages = get_messages(chat_id)

for message in messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ================= IMAGE ENCODING =================
def image_data_url(blob, mime):

    encoded = base64.b64encode(blob).decode("utf-8")

    return (
        f"data:{mime or 'image/jpeg'};"
        f"base64,{encoded}"
    )


# ================= GROQ AI =================
def groq_answer(question, image_blob, image_mime, history):

    api_key = st.secrets.get("GROQ_API_KEY", "")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing in Streamlit Secrets."
        )

    api_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Previous conversation
    for message in history:

        api_messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    # Current question and image
    current_content = [
        {
            "type": "text",
            "text": question
        }
    ]

    if image_blob:

        current_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_data_url(
                    image_blob,
                    image_mime
                )
            }
        })

    api_messages.append({
        "role": "user",
        "content": current_content
    })

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": api_messages,
            "temperature": 0.25,
            "max_tokens": 1200
        },
        timeout=120
    )

    if not response.ok:

        try:
            detail = response.json().get(
                "error", {}
            ).get(
                "message", response.text
            )
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"Groq API ({response.status_code}): {detail}"
        )

    return response.json()["choices"][0]["message"]["content"].strip()


# ================= CHAT INPUT =================
question = st.chat_input(
    "Ask CrackGPT about the structural damage..."
)

if question:

    if not image_blob:

        st.warning("Please upload an image first.")

    else:

        # Save current question
        save_message(chat_id, "user", question)
        update_title(chat_id, question)

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Examining the image and preparing an engineering answer..."
            ):

                try:

                    # Exclude current question from history
                    prior_messages = get_messages(chat_id)[:-1]

                    answer = groq_answer(
                        question,
                        image_blob,
                        image_mime,
                        prior_messages
                    )

                    st.markdown(answer)

                    # Save AI response
                    save_message(
                        chat_id,
                        "assistant",
                        answer
                    )

                except Exception as error:

                    st.error(str(error))
