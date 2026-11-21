
import streamlit as st
import requests
import sqlite3
import base64
import uuid
from datetime import datetime
from PIL import Image
from io import BytesIO

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

DB_PATH = "crackgpt_chat_history.db"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """
You are CrackGPT, a visual structural-damage discussion assistant.

STRICT RESPONSE RULES:
1. Answer ONLY the user's current question.
2. Do not provide a full structural assessment unless explicitly requested.
3. Do not answer questions the user did not ask.
4. Do not add unsolicited sections such as causes, risks, repairs,
   recommendations, inspection advice, or summaries.
5. Keep answers concise, direct, and relevant.
6. Use the uploaded image as evidence when available.
7. Describe visible observations separately from possible explanations.
8. Never invent dimensions, materials, reinforcement, corrosion,
   severity, or structural safety.
9. If the image does not provide enough evidence, clearly say so.
10. Maintain conversation context for follow-up questions.
11. If the user asks for a location, answer only the location question.
12. If the user asks for damage type, answer only the damage type.
13. If the user asks for causes, discuss causes only.
14. If the user asks for repair suggestions, discuss repairs only.
15. Do not repeat previous answers unless the user requests it.

For safety-related questions, explain briefly that image-based
assessment alone cannot confirm structural safety.
"""

# ============================================================
# DATABASE
# ============================================================

def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")

    # Create tables if they do not exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            image BLOB,
            image_type TEXT,
            created TEXT,
            updated TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            created TEXT
        )
    """)

    # --------------------------------------------------------
    # AUTOMATIC DATABASE MIGRATION
    # Fixes older databases missing columns
    # --------------------------------------------------------

    chat_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(chats)").fetchall()
    }

    required_chat_columns = {
        "title": "TEXT DEFAULT 'New conversation'",
        "image": "BLOB",
        "image_type": "TEXT",
        "created": "TEXT",
        "updated": "TEXT"
    }

    for column, definition in required_chat_columns.items():
        if column not in chat_columns:
            conn.execute(
                f"ALTER TABLE chats ADD COLUMN {column} {definition}"
            )

    message_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()
    }

    required_message_columns = {
        "chat_id": "TEXT",
        "role": "TEXT",
        "content": "TEXT",
        "created": "TEXT"
    }

    for column, definition in required_message_columns.items():
        if column not in message_columns:
            conn.execute(
                f"ALTER TABLE messages ADD COLUMN {column} {definition}"
            )

    # Repair missing timestamps in old conversations
    now = datetime.now().isoformat(timespec="seconds")

    conn.execute("""
        UPDATE chats
        SET created = ?
        WHERE created IS NULL OR created = ''
    """, (now,))

    conn.execute("""
        UPDATE chats
        SET updated = created
        WHERE updated IS NULL OR updated = ''
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_chat_id
        ON messages(chat_id)
    """)

    conn.commit()
    return conn


def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

    try:
        conn.execute("""
            INSERT INTO chats
            (id, title, image, image_type, created, updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            "New conversation",
            None,
            None,
            now,
            now
        ))

        conn.commit()
    finally:
        conn.close()

    return chat_id


def list_chats():
    conn = db_connect()

    try:
        chats = conn.execute("""
            SELECT id, title, updated
            FROM chats
            ORDER BY updated DESC
        """).fetchall()

        return chats
    finally:
        conn.close()


def get_chat(chat_id):
    conn = db_connect()

    try:
        return conn.execute("""
            SELECT id, title, image, image_type
            FROM chats
            WHERE id = ?
        """, (chat_id,)).fetchone()
    finally:
        conn.close()


def save_image(chat_id, image_bytes, mime_type):
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

    try:
        conn.execute("""
            UPDATE chats
            SET image = ?, image_type = ?, updated = ?
            WHERE id = ?
        """, (image_bytes, mime_type, now, chat_id))

        conn.commit()
    finally:
        conn.close()


def remove_image(chat_id):
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

    try:
        conn.execute("""
            UPDATE chats
            SET image = NULL, image_type = NULL, updated = ?
            WHERE id = ?
        """, (now, chat_id))

        conn.commit()
    finally:
        conn.close()


def save_message(chat_id, role, content):
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

    try:
        conn.execute("""
            INSERT INTO messages
            (chat_id, role, content, created)
            VALUES (?, ?, ?, ?)
        """, (chat_id, role, content, now))

        conn.execute("""
            UPDATE chats
            SET updated = ?
            WHERE id = ?
        """, (now, chat_id))

        conn.commit()
    finally:
        conn.close()


def get_messages(chat_id):
    conn = db_connect()

    try:
        return conn.execute("""
            SELECT role, content
            FROM messages
            WHERE chat_id = ?
            ORDER BY id ASC
        """, (chat_id,)).fetchall()
    finally:
        conn.close()


def set_chat_title(chat_id, title):
    title = title.strip()

    if not title:
        return

    conn = db_connect()

    try:
        conn.execute("""
            UPDATE chats
            SET title = ?
            WHERE id = ?
              AND title = 'New conversation'
        """, (title[:55], chat_id))

        conn.commit()
    finally:
        conn.close()


# ============================================================
# IMAGE UTILITIES
# ============================================================

def image_data_url(image_bytes, mime_type):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def compress_image(uploaded_file):
    """
    Convert uploaded image to JPEG for efficient storage and API transfer.
    """

    image = Image.open(uploaded_file).convert("RGB")

    # Resize very large images while preserving aspect ratio
    max_dimension = 1600

    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension))

    output = BytesIO()
    image.save(output, format="JPEG", quality=85, optimize=True)

    return output.getvalue(), "image/jpeg"


# ============================================================
# GROQ AI
# ============================================================

def ask_groq(question, image_bytes, mime_type, history):

    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
        model = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)

    except Exception:
        api_key = ""
        model = DEFAULT_MODEL

    if not api_key:
        return (
            "Groq API key is missing.\n\n"
            "Please add GROQ_API_KEY in your Streamlit secrets."
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Include previous conversation context
    for role, content in history[-12:]:

        if role in ("user", "assistant"):

            messages.append({
                "role": role,
                "content": content
            })

    # Current user message
    user_content = [
        {
            "type": "text",
            "text": question
        }
    ]

    # Attach the current chat image
    if image_bytes:

        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": image_data_url(
                    image_bytes,
                    mime_type or "image/jpeg"
                )
            }
        })

    messages.append({
        "role": "user",
        "content": user_content
    })

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1200
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:

            try:
                error_message = response.json().get("error", {}).get(
                    "message", response.text
                )
            except Exception:
                error_message = response.text

            return f"Groq API Error ({response.status_code}):\n{error_message}"

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        if isinstance(answer, list):

            answer = "\n".join(
                item.get("text", "")
                for item in answer
                if item.get("type") == "text"
            )

        return answer.strip()

    except requests.exceptions.Timeout:

        return "The AI response timed out. Please try again."

    except requests.exceptions.ConnectionError:

        return "Unable to connect to Groq. Please check your internet connection."

    except Exception as e:

        return f"Unexpected error: {str(e)}"


# ============================================================
# SESSION INITIALIZATION
# ============================================================

if "active_chat_id" not in st.session_state:

    existing_chats = list_chats()

    if existing_chats:
        st.session_state.active_chat_id = existing_chats[0][0]
    else:
        st.session_state.active_chat_id = create_chat()


if "processing" not in st.session_state:
    st.session_state.processing = False


active_chat_id = st.session_state.active_chat_id


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("""
    <div style="padding-top:10px;">
        <h2>🏗️ CrackGPT</h2>
        <p style="color:gray;">Structural Intelligence Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # New Chat button
    if st.button("＋ New Chat", use_container_width=True):

        new_id = create_chat()

        st.session_state.active_chat_id = new_id

        st.rerun()

    st.divider()

    st.markdown("### 💬 Chat History")

    chats = list_chats()

    if chats:

        for chat_id, title, updated in chats:

            display_title = title or "New conversation"

            is_active = chat_id == st.session_state.active_chat_id

            button_label = (
                f"📌 {display_title}"
                if is_active
                else f"💬 {display_title}"
            )

            if st.button(
                button_label,
                key=f"chat_{chat_id}",
                use_container_width=True
            ):

                st.session_state.active_chat_id = chat_id

                st.rerun()

    else:

        st.caption("No conversations yet.")

    st.divider()

    st.caption(
        "CrackGPT provides image-based structural observations "
        "and is not a substitute for professional inspection."
    )


# ============================================================
# LOAD CURRENT CHAT
# ============================================================

active_chat_id = st.session_state.active_chat_id

chat_data = get_chat(active_chat_id)

if chat_data is None:

    active_chat_id = create_chat()

    st.session_state.active_chat_id = active_chat_id

    chat_data = get_chat(active_chat_id)


chat_id, chat_title, stored_image, stored_image_type = chat_data

messages_history = get_messages(chat_id)


# ============================================================
# MAIN INTERFACE
# ============================================================

st.title("🏗️ CrackGPT")

st.subheader("Structural Intelligence Assistant")

st.write(
    "Upload a structural image and ask questions about visible damage "
    "patterns, cracks, or structural observations."
)

st.divider()


# ============================================================
# IMAGE UPLOAD
# ============================================================

st.markdown("### 📷 Upload a structural image")

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp"],
    key=f"image_upload_{chat_id}",
    label_visibility="collapsed"
)


# Save uploaded image
if uploaded_file is not None:

    try:

        image_bytes, image_type = compress_image(uploaded_file)

        save_image(
            chat_id,
            image_bytes,
            image_type
        )

        st.rerun()

    except Exception as e:

        st.error(f"Unable to process image: {e}")


# Reload chat image after upload
chat_data = get_chat(chat_id)

if chat_data:

    stored_image = chat_data[2]
    stored_image_type = chat_data[3]


# Display uploaded image
if stored_image:

    st.image(
        stored_image,
        caption="Uploaded structural image",
        use_container_width=True
    )

    if st.button("🗑️ Remove image", key=f"remove_image_{chat_id}"):

        remove_image(chat_id)

        st.rerun()


# ============================================================
# DISPLAY CHAT HISTORY
# ============================================================

for role, content in messages_history:

    if role == "user":

        with st.chat_message("user"):

            st.markdown(content)

    elif role == "assistant":

        with st.chat_message("assistant"):

            st.markdown(content)


# ============================================================
# CHAT INPUT
# ============================================================

question = st.chat_input(
    "Ask CrackGPT about your image..."
)


if question:

    question = question.strip()

    if question:

        # Save current question
        save_message(
            chat_id,
            "user",
            question
        )

        # Automatically create title from first question
        set_chat_title(
            chat_id,
            question
        )

        # History before the current question
        previous_history = messages_history

        # Show current user message
        with st.chat_message("user"):

            st.markdown(question)

        # AI response
        with st.chat_message("assistant"):

            with st.spinner("Analyzing your question..."):

                answer = ask_groq(
                    question=question,
                    image_bytes=stored_image,
                    mime_type=stored_image_type,
                    history=previous_history
                )

            st.markdown(answer)

        # Save AI response
        save_message(
            chat_id,
            "assistant",
            answer
        )

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CrackGPT provides image-based structural observations. "
    "Image-based analysis alone cannot determine structural safety."
)
