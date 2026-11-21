
import streamlit as st
import requests
import sqlite3
import base64
import uuid
import os
from datetime import datetime

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

DB_PATH = "crackgpt_chat_history.db"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """
You are CrackGPT, an AI assistant specialized in visual structural
damage understanding and structural engineering discussions.

STRICT QUESTION-ANSWERING BEHAVIOR:

- Answer ONLY the question currently asked by the user.
- Do not answer questions that the user did not ask.
- Never automatically generate a complete damage assessment.
- Never add causes, severity, risks, repairs, recommendations,
  inspection procedures, or conclusions unless requested.
- Do not repeat information already provided unless requested.
- Keep answers concise, clear, and technically useful.
- For simple questions, answer in 1-3 sentences.
- If the user says "in short", provide a very short answer.
- If the user asks for a location, mention only the damage location.
- If the user asks about damage type, identify only the visible damage.
- If the user asks about causes, discuss possible causes only.
- If the user asks about severity, discuss severity only.
- If the user asks about repair, discuss repair only.
- Provide a complete assessment only when explicitly requested.

IMAGE RULES:

- Use the uploaded image as evidence.
- Describe only details that can reasonably be observed.
- Do not invent cracks, corrosion, reinforcement, dimensions,
  materials, damage, or structural conditions.
- Do not assume a material type unless reasonably identifiable.
- Distinguish visible observations from possible explanations.
- If something cannot be confirmed, say so briefly.

CONVERSATION RULES:

- Maintain context across the conversation.
- Remember the uploaded image when answering follow-up questions.
- Understand short follow-ups such as "where?", "why?", "which part?",
  "how severe?", and "in short".
- Do not restart the assessment for every new question.
- Answer the current question directly.

SAFETY:

- Never declare a structure safe or unsafe based only on images.
- Mention professional inspection only when relevant to the question.

RESPONSE STYLE:

- Direct answer first.
- No unnecessary headings.
- No unnecessary bullet points.
- No long explanations unless requested.
- Do not add a summary at the end.
- Do not ask unnecessary follow-up questions.
- Answer only what is needed.
"""

# =========================================================
# DATABASE AND AUTOMATIC MIGRATION
# =========================================================

def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)

    conn.execute("PRAGMA journal_mode=WAL")

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

    # ---------------------------------------------
    # Repair old chats table automatically
    # ---------------------------------------------

    chat_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(chats)").fetchall()
    }

    required_chat_columns = {
        "title": "TEXT",
        "image": "BLOB",
        "image_type": "TEXT",
        "created": "TEXT",
        "updated": "TEXT"
    }

    for column, datatype in required_chat_columns.items():
        if column not in chat_columns:
            conn.execute(
                f"ALTER TABLE chats ADD COLUMN {column} {datatype}"
            )

    # ---------------------------------------------
    # Repair old messages table automatically
    # ---------------------------------------------

    message_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(messages)").fetchall()
    }

    required_message_columns = {
        "chat_id": "TEXT",
        "role": "TEXT",
        "content": "TEXT",
        "created": "TEXT"
    }

    for column, datatype in required_message_columns.items():
        if column not in message_columns:
            conn.execute(
                f"ALTER TABLE messages ADD COLUMN {column} {datatype}"
            )

    # ---------------------------------------------
    # Repair existing chat timestamps
    # ---------------------------------------------

    conn.execute("""
        UPDATE chats
        SET created = COALESCE(created, datetime('now'))
        WHERE created IS NULL
    """)

    conn.execute("""
        UPDATE chats
        SET updated = COALESCE(updated, created, datetime('now'))
        WHERE updated IS NULL
    """)

    conn.commit()

    return conn


# =========================================================
# CHAT MANAGEMENT
# =========================================================

def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

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
    conn.close()

    return chat_id


def list_chats():
    conn = db_connect()

    chats = conn.execute("""
        SELECT id, title, updated
        FROM chats
        ORDER BY updated DESC
    """).fetchall()

    conn.close()

    return chats


def get_chat(chat_id):
    conn = db_connect()

    chat = conn.execute("""
        SELECT id, title, image, image_type
        FROM chats
        WHERE id = ?
    """, (chat_id,)).fetchone()

    conn.close()

    return chat


def save_image(chat_id, image_bytes, mime_type):
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

    conn.execute("""
        UPDATE chats
        SET image = ?,
            image_type = ?,
            updated = ?
        WHERE id = ?
    """, (image_bytes, mime_type, now, chat_id))

    conn.commit()
    conn.close()


def save_message(chat_id, role, content):
    now = datetime.now().isoformat(timespec="seconds")

    conn = db_connect()

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
    conn.close()


def get_messages(chat_id):
    conn = db_connect()

    messages = conn.execute("""
        SELECT role, content
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
    """, (chat_id,)).fetchall()

    conn.close()

    return messages


def set_chat_title(chat_id, title):
    conn = db_connect()

    conn.execute("""
        UPDATE chats
        SET title = ?
        WHERE id = ?
        AND title = 'New conversation'
    """, (title[:55], chat_id))

    conn.commit()
    conn.close()


# =========================================================
# IMAGE PROCESSING
# =========================================================

def image_data_url(image_bytes, mime_type):
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# =========================================================
# GROQ AI
# =========================================================

def ask_groq(question, image_bytes, mime_type, history):

    api_key = st.secrets.get(
        "GROQ_API_KEY",
        os.environ.get("GROQ_API_KEY", "")
    )

    model = st.secrets.get(
        "GROQ_MODEL",
        DEFAULT_MODEL
    )

    if not api_key:
        return (
            "Groq API key is missing. "
            "Please add GROQ_API_KEY in Streamlit Secrets."
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Add recent conversation context
    for role, content in history[-10:]:

        if role in ("user", "assistant"):

            messages.append({
                "role": role,
                "content": content
            })

    # Current user question
    user_content = [
        {
            "type": "text",
            "text": question
        }
    ]

    # Attach image if available
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
        "temperature": 0.2,
        "max_tokens": 350
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

        response.raise_for_status()

        data = response.json()

        answer = data["choices"][0]["message"]["content"]

        return answer.strip()

    except requests.exceptions.Timeout:

        return "The request timed out. Please try again."

    except requests.exceptions.HTTPError:

        try:
            error_message = response.json().get("error", {}).get("message", "")
        except Exception:
            error_message = response.text[:500]

        return f"AI API error: {error_message}"

    except Exception as e:

        return f"Something went wrong: {str(e)}"


# =========================================================
# SESSION STATE
# =========================================================

if "chat_id" not in st.session_state:

    chats = list_chats()

    if chats:
        st.session_state.chat_id = chats[0][0]
    else:
        st.session_state.chat_id = create_chat()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("# 🏗️ CrackGPT")

    st.caption("Structural Intelligence Assistant")

    st.divider()

    # New chat button
    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        st.session_state.chat_id = create_chat()

        st.rerun()

    st.divider()

    st.markdown("### 💬 Chat History")

    chats = list_chats()

    for chat_id, title, updated in chats:

        display_title = title or "New conversation"

        if st.button(
            f"💬 {display_title}",
            key=f"chat_{chat_id}",
            use_container_width=True
        ):

            st.session_state.chat_id = chat_id

            st.rerun()


# =========================================================
# LOAD CURRENT CHAT
# =========================================================

current_chat = get_chat(st.session_state.chat_id)

if current_chat is None:

    st.session_state.chat_id = create_chat()

    st.rerun()


chat_id, chat_title, saved_image, saved_image_type = current_chat


# =========================================================
# MAIN INTERFACE
# =========================================================

st.title("🏗️ CrackGPT")

st.markdown("### Structural Intelligence Assistant")

st.write(
    "Upload a structural image and ask questions about visible "
    "damage patterns, cracks, or structural observations."
)

st.divider()


# =========================================================
# IMAGE UPLOAD
# =========================================================

st.markdown("📷 **Upload a structural image**")

uploaded_image = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed",
    key=f"uploader_{chat_id}"
)


# Use saved image if no new image is uploaded
image_bytes = saved_image
image_type = saved_image_type


# Save newly uploaded image
if uploaded_image is not None:

    new_image_bytes = uploaded_image.getvalue()

    # Save only if image has changed
    if new_image_bytes != saved_image:

        image_bytes = new_image_bytes
        image_type = uploaded_image.type

        save_image(
            chat_id,
            image_bytes,
            image_type
        )

    else:

        image_bytes = saved_image
        image_type = saved_image_type


# Display current image
if image_bytes:

    st.image(
        image_bytes,
        caption="Image attached to this conversation",
        use_container_width=True
    )

    if st.button(
        "Remove image from this conversation",
        key=f"remove_image_{chat_id}"
    ):

        save_image(chat_id, None, None)

        st.rerun()


st.divider()


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

chat_history = get_messages(chat_id)

for role, content in chat_history:

    with st.chat_message(role):

        st.markdown(content)


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask CrackGPT about your image..."
)


if question:

    # Save first user question as chat title
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

    # Show user message immediately
    with st.chat_message("user"):

        st.markdown(question)

    # Get conversation context before AI response
    history = get_messages(chat_id)

    # Remove the current question from history
    history = history[:-1]

    # Generate answer
    with st.chat_message("assistant"):

        with st.spinner("CrackGPT is thinking..."):

            answer = ask_groq(
                question=question,
                image_bytes=image_bytes,
                mime_type=image_type,
                history=history
            )

        st.markdown(answer)

    # Save assistant response
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
