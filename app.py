
import streamlit as st
import requests
import sqlite3
import base64
import uuid
from datetime import datetime
from PIL import Image
from io import BytesIO

# =========================================================
# CONFIG
# =========================================================
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

Answer ONLY the user's current question.
Do not automatically provide a complete assessment.

Use uploaded images as evidence.
Describe only details that can reasonably be seen.
Clearly distinguish visible observations from possible explanations.

Do not invent:
- Material type
- Reinforcement exposure
- Corrosion
- Crack dimensions
- Crack depth
- Structural severity
- Structural safety

If something cannot be confirmed from the image, say so.

Keep answers concise, clear, and technically useful.

For structural safety decisions, explain that image-based assessment
alone is insufficient and an engineer/site inspection may be needed.

Maintain conversation context so follow-up questions refer to the
same image and previous answers.

Only provide a complete structural damage assessment if the
user explicitly asks for one.
"""

# =========================================================
# DATABASE + AUTOMATIC SCHEMA REPAIR
# =========================================================
def db_connect():

    conn = sqlite3.connect(DB_PATH, timeout=30)

    conn.execute("PRAGMA journal_mode=WAL")

    # Create chats table if it does not exist
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

    # Create messages table if it does not exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            created TEXT
        )
    """)

    # -------- Repair chats table --------
    chat_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(chats)").fetchall()
    }

    chat_required_columns = {
        "title": "TEXT",
        "image": "BLOB",
        "image_type": "TEXT",
        "created": "TEXT",
        "updated": "TEXT"
    }

    for column, column_type in chat_required_columns.items():

        if column not in chat_columns:

            conn.execute(
                f"ALTER TABLE chats ADD COLUMN {column} {column_type}"
            )

    # -------- Repair messages table --------
    message_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(messages)").fetchall()
    }

    message_required_columns = {
        "chat_id": "TEXT",
        "role": "TEXT",
        "content": "TEXT",
        "created": "TEXT"
    }

    for column, column_type in message_required_columns.items():

        if column not in message_columns:

            conn.execute(
                f"ALTER TABLE messages ADD COLUMN {column} {column_type}"
            )

    # Repair missing IDs if older schema lacks them
    chat_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(chats)").fetchall()
    }

    if "id" not in chat_columns:

        conn.execute("ALTER TABLE chats ADD COLUMN id TEXT")

        rows = conn.execute(
            "SELECT rowid FROM chats"
        ).fetchall()

        for row in rows:

            conn.execute(
                "UPDATE chats SET id=? WHERE rowid=?",
                (str(uuid.uuid4()), row[0])
            )

    message_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(messages)").fetchall()
    }

    if "id" not in message_columns:

        conn.execute("ALTER TABLE messages ADD COLUMN id INTEGER")

        rows = conn.execute(
            "SELECT rowid FROM messages"
        ).fetchall()

        for row in rows:

            conn.execute(
                "UPDATE messages SET id=? WHERE rowid=?",
                (row[0], row[0])
            )

    # Fill empty timestamps
    now = datetime.now().isoformat(timespec="seconds")

    conn.execute(
        "UPDATE chats SET created=? WHERE created IS NULL",
        (now,)
    )

    conn.execute(
        "UPDATE chats SET updated=? WHERE updated IS NULL",
        (now,)
    )

    conn.execute(
        "UPDATE chats SET title='New conversation' WHERE title IS NULL"
    )

    conn.execute(
        "UPDATE messages SET created=? WHERE created IS NULL",
        (now,)
    )

    conn.commit()

    return conn


# Run database initialization and repair
try:
    with db_connect() as conn:
        pass
except Exception as e:
    st.error(f"Database initialization error: {e}")
    st.stop()


# =========================================================
# CHAT DATABASE FUNCTIONS
# =========================================================
def create_chat():

    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    with db_connect() as conn:

        conn.execute(
            """
            INSERT INTO chats
            (id, title, image, image_type, created, updated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                "New conversation",
                None,
                None,
                now,
                now
            )
        )

    return chat_id


def list_chats():

    with db_connect() as conn:

        return conn.execute(
            """
            SELECT id, title, updated
            FROM chats
            ORDER BY updated DESC
            """
        ).fetchall()


def get_chat(chat_id):

    with db_connect() as conn:

        return conn.execute(
            """
            SELECT id, title, image, image_type
            FROM chats
            WHERE id=?
            """,
            (chat_id,)
        ).fetchone()


def save_image(chat_id, image_bytes, mime_type):

    now = datetime.now().isoformat(timespec="seconds")

    with db_connect() as conn:

        conn.execute(
            """
            UPDATE chats
            SET image=?, image_type=?, updated=?
            WHERE id=?
            """,
            (
                image_bytes,
                mime_type,
                now,
                chat_id
            )
        )


def save_message(chat_id, role, content):

    now = datetime.now().isoformat(timespec="seconds")

    with db_connect() as conn:

        conn.execute(
            """
            INSERT INTO messages
            (chat_id, role, content, created)
            VALUES (?, ?, ?, ?)
            """,
            (
                chat_id,
                role,
                content,
                now
            )
        )

        conn.execute(
            "UPDATE chats SET updated=? WHERE id=?",
            (now, chat_id)
        )


def get_messages(chat_id):

    with db_connect() as conn:

        return conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE chat_id=?
            ORDER BY id
            """,
            (chat_id,)
        ).fetchall()


def set_chat_title(chat_id, title):

    title = title.replace("\n", " ").strip()

    if not title:
        title = "New conversation"

    with db_connect() as conn:

        conn.execute(
            """
            UPDATE chats
            SET title=?
            WHERE id=? AND title='New conversation'
            """,
            (title[:55], chat_id)
        )


def delete_chat(chat_id):

    with db_connect() as conn:

        conn.execute(
            "DELETE FROM messages WHERE chat_id=?",
            (chat_id,)
        )

        conn.execute(
            "DELETE FROM chats WHERE id=?",
            (chat_id,)
        )


# =========================================================
# IMAGE UTILITIES
# =========================================================
def image_data_url(image_bytes, mime_type):

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def prepare_image(uploaded_file):

    if uploaded_file is None:
        return None, None

    image = Image.open(uploaded_file)

    if image.mode != "RGB":
        image = image.convert("RGB")

    max_dimension = 1600

    if max(image.size) > max_dimension:

        image.thumbnail(
            (max_dimension, max_dimension)
        )

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=85
    )

    return output.getvalue(), "image/jpeg"


# =========================================================
# GROQ AI
# =========================================================
def ask_groq(question, image_bytes, mime_type, history):

    api_key = st.secrets.get("GROQ_API_KEY", "")
    model = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)

    if not api_key:

        return (
            "⚠️ Groq API key is missing. "
            "Add GROQ_API_KEY in Streamlit Secrets."
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Add previous conversation context
    for role, content in history[-12:]:

        if role in ("user", "assistant"):

            messages.append({
                "role": role,
                "content": content
            })

    # Current message
    user_content = [
        {
            "type": "text",
            "text": question
        }
    ]

    # Add image if available
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
        "max_tokens": 1024
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

            return (
                f"⚠️ Groq API error ({response.status_code})\n\n"
                f"{response.text[:1000]}"
            )

        result = response.json()

        return result["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:

        return "⚠️ AI request timed out. Please try again."

    except requests.exceptions.RequestException as e:

        return f"⚠️ Network error: {str(e)}"

    except Exception as e:

        return f"⚠️ Unexpected error: {str(e)}"


# =========================================================
# SESSION STATE
# =========================================================
if "active_chat" not in st.session_state:

    st.session_state.active_chat = None

if "pending_image" not in st.session_state:

    st.session_state.pending_image = None

if "pending_image_type" not in st.session_state:

    st.session_state.pending_image_type = None


# =========================================================
# INITIAL CHAT
# =========================================================
chats = list_chats()

if not chats:

    st.session_state.active_chat = create_chat()

elif st.session_state.active_chat is None:

    st.session_state.active_chat = chats[0][0]


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.title("🏗️ CrackGPT")

    st.caption("Structural Intelligence Assistant")

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        new_chat_id = create_chat()

        st.session_state.active_chat = new_chat_id
        st.session_state.pending_image = None
        st.session_state.pending_image_type = None

        st.rerun()

    st.divider()

    st.subheader("💬 Chat History")

    chats = list_chats()

    for chat_id, title, updated in chats:

        active = chat_id == st.session_state.active_chat

        label = (
            f"📍 {title}"
            if active
            else f"💬 {title}"
        )

        if st.button(
            label,
            key=f"select_{chat_id}",
            use_container_width=True
        ):

            st.session_state.active_chat = chat_id

            st.session_state.pending_image = None
            st.session_state.pending_image_type = None

            st.rerun()

    st.divider()

    st.caption("CrackGPT V8")


# =========================================================
# LOAD ACTIVE CHAT
# =========================================================
chat = get_chat(st.session_state.active_chat)

if chat is None:

    st.session_state.active_chat = create_chat()

    st.rerun()

chat_id, chat_title, saved_image, saved_image_type = chat


# =========================================================
# MAIN UI
# =========================================================
st.title("🏗️ CrackGPT")

st.markdown("### Structural Intelligence Assistant")

st.write(
    "Upload a crack image and ask questions about visible "
    "damage patterns, cracks, or structural observations."
)

st.divider()


# =========================================================
# IMAGE UPLOAD
# =========================================================
uploaded_file = st.file_uploader(
    "📷 Upload a structural image",
    type=["jpg", "jpeg", "png", "webp"],
    key=f"upload_{chat_id}"
)

if uploaded_file is not None:

    image_bytes, image_type = prepare_image(uploaded_file)

    if image_bytes:

        st.session_state.pending_image = image_bytes
        st.session_state.pending_image_type = image_type

        save_image(
            chat_id,
            image_bytes,
            image_type
        )


# Reload saved image
chat = get_chat(chat_id)

saved_image = chat[2]
saved_image_type = chat[3]

current_image = (
    st.session_state.pending_image
    if st.session_state.pending_image is not None
    else saved_image
)

current_image_type = (
    st.session_state.pending_image_type
    if st.session_state.pending_image_type is not None
    else saved_image_type
)


# =========================================================
# DISPLAY IMAGE
# =========================================================
if current_image:

    with st.expander(
        "🖼️ Uploaded Image",
        expanded=True
    ):

        st.image(
            Image.open(BytesIO(current_image)),
            caption="Image used for this conversation",
            use_container_width=True
        )


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================
history = get_messages(chat_id)

for role, content in history:

    if role not in ("user", "assistant"):
        continue

    with st.chat_message(role):

        st.markdown(content)


# =========================================================
# CHAT INPUT
# =========================================================
question = st.chat_input(
    "Ask CrackGPT about your image..."
)


# =========================================================
# PROCESS USER MESSAGE
# =========================================================
if question:

    # Create conversation title from first question
    if chat_title == "New conversation":

        set_chat_title(
            chat_id,
            question
        )

    # Save user message
    save_message(
        chat_id,
        "user",
        question
    )

    with st.chat_message("user"):

        st.markdown(question)

        if current_image:

            st.caption("📷 Image attached")


    # AI response
    with st.chat_message("assistant"):

        with st.spinner("CrackGPT is thinking..."):

            answer = ask_groq(
                question,
                current_image,
                current_image_type,
                history
            )

        st.markdown(answer)

    # Save assistant answer
    save_message(
        chat_id,
        "assistant",
        answer
    )

    st.rerun()


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "CrackGPT provides image-based structural observations "
    "and is not a substitute for professional inspection."
)

