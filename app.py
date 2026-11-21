                import streamlit as st
import requests
import sqlite3
import base64
import uuid
from datetime import datetime

# -------------------- CONFIG --------------------
st.set_page_config(page_title="CrackGPT | Structural Intelligence", page_icon="🏗️", layout="wide")
DB_PATH = "crackgpt_chat_history.db"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """\
You are CrackGPT, an AI assistant specialized in visual identification of structural damage, corrosion, and material deterioration.

PRIMARY TASK:
Analyze the uploaded image and answer the user's exact question using visible evidence and structural engineering terminology.

1. MATERIAL IDENTIFICATION
- Identify the material before classifying the damage.
- Distinguish concrete, reinforced concrete, steel, painted metal, masonry, and other visible materials.
- Never assume a rusty surface is reinforcement.
- Never identify rebar unless it is visible or clearly supported by the image.
- Never assume concrete is present when it is not visible.

2. DAMAGE IDENTIFICATION
Recognize relevant damage types when supported, including concrete cracking, spalling, delamination, honeycombing, scaling, reinforcement corrosion, surface rust, uniform corrosion, pitting corrosion, crevice corrosion, coating failure, paint peeling, moisture staining, water seepage, efflorescence, masonry deterioration, deformation, and other material deterioration.

3. IMAGE-BASED OBSERVATIONS
- Identify the actual visible damage whenever evidence supports it.
- Describe location, pattern, shape, orientation, color, and extent when asked.
- Distinguish rust staining from confirmed metal corrosion.
- Distinguish surface cracks from concrete spalling.
- Do not claim exposed reinforcement unless steel is visible.
- Do not claim concrete spalling if concrete is not visible.
- Do not invent cracks, pits, cavities, moisture, or missing material.

4. CAUSES
- Explain possible causes only when the user asks.
- Present causes as possibilities unless confirmed.
- Consider moisture, oxygen, chloride exposure, carbonation, environmental exposure, poor workmanship, material defects, loading, and other relevant factors when appropriate.
- Never claim a specific cause based solely on an image.

5. STRUCTURAL EFFECTS
- Explain possible effects on strength, durability, serviceability, and structural performance only when requested.
- Do not declare a structure safe or unsafe based only on images.

6. PRECAUTIONS AND PREVENTION
- Give precautions only when requested.
- Provide recommendations relevant to the identified material and damage.
- Avoid generic recommendations unrelated to the image.

7. REPAIR AND TREATMENT
- Suggest suitable repair or treatment methods only when asked.
- Distinguish superficial damage from potentially deeper deterioration.
- Do not recommend a specific repair without considering material, damage extent, and limitations of image-based assessment.

8. QUESTION-SPECIFIC ANSWERING
- Answer ONLY the question asked by the user.
- Do not automatically generate a complete damage assessment.
- Do not repeat previous answers unnecessarily.
- Do not include causes, severity, risks, precautions, or treatments unless explicitly requested.
- Maintain context for follow-up questions about the same image.

9. RESPONSE STYLE
- Use clear, simple, technically accurate language.
- Keep answers concise, preferably 1-2 sentences.
- Avoid unnecessary headings, bullet points, and lengthy explanations.
- Use specific engineering terminology instead of vague descriptions.
- If something cannot be confirmed visually, state the uncertainty briefly.

10. ACCURACY
- Never fabricate observations.
- Never overstate confidence.
- Separate visible evidence from engineering interpretation.
- If the image is insufficient, clearly say what cannot be determined.
"""

# -------------------- DATABASE + MIGRATION --------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn



def init_db():
    with db_connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT 'New conversation',
            image BLOB,
            image_type TEXT,
            created TEXT,
             updated TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            created TEXT
        )""")

        # Migrate older database versions without deleting existing chats.
        chat_cols = {row[1] for row in conn.execute("PRAGMA table_info(chats)").fetchall()}
        migrations = {
            "title": "ALTER TABLE chats ADD COLUMN title TEXT DEFAULT 'New conversation'",
            "image": "ALTER TABLE chats ADD COLUMN image BLOB",
            "image_type": "ALTER TABLE chats ADD COLUMN image_type TEXT",
            "created": "ALTER TABLE chats ADD COLUMN created TEXT",
            "updated": "ALTER TABLE chats ADD COLUMN updated TEXT",
        }
                        conn.execute(sql)

        # Fill timestamp fields in old records so sorting works.
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE chats SET created=COALESCE(created, ?) WHERE created IS NULL", (now,))
        conn.execute("UPDATE chats SET updated=COALESCE(updated, created, ?) WHERE updated IS NULL", (now,))
        conn.commit()


def create_chat():
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO chats (id,title,image,image_type,created,updated) VALUES (?,?,?,?,?,?)",
            (chat_id, "New conversation", None, None, now, now)
        )
    return chat_id



def list_chats():
    with db_connect() as conn:
        return conn.execute("SELECT id,title,updated FROM chats ORDER BY updated DESC").fetchall()



def get_chat(chat_id):
    with db_connect() as conn:
        return conn.execute("SELECT id,title,image,image_type FROM chats WHERE id=?", (chat_id,)).fetchone()



def save_image(chat_id, image_bytes, mime_type):
    now = datetime.now().isoformat(timespec="seconds")
    with db_connect() as conn:
        conn.execute("UPDATE chats SET image=?, image_type=?, updated=? WHERE id=?",
                   (image_bytes, mime_type, now, chat_id))


def save_message(chat_id, role, content):
    now = datetime.now().isoformat(timespec="seconds")
    with db_connect() as conn:
        conn.execute("INSERT INTO messages (chat_id,role,content,created) VALUES (?,?,?,?)",
                   (chat_id, role, content, now))
        conn.execute("UPDATE chats SET updated=? WHERE id=?", (now, chat_id))


def get_messages(chat_id):
    with db_connect() as conn:
        return conn.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id", (chat_id,)).fetchall()



def set_chat_title(chat_id, title):
    clean_title = " ".join(title.strip().split())[:55] or "New conversation"
    now = datetime.now().isoformat(timespec="seconds")
    with db_connect() as conn:
        conn.execute("UPDATE chats SET title=?,updated=? WHERE id=? AND title='New conversation'",
                   (clean_title, now, chat_id))

# -------------------- AI --------------------
def image_data_url(image_bytes, mime_type):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"



def ask_groq(question, image_bytes, mime_type, history):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    model = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)
    if not api_key:
        return "Groq API key is missing. Add GROQ_API_KEY in Streamlit Secrets."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Use only the most recent exchange to limit input tokens.
    for role, content in history[-2:]:
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    user_content = [{"type": "text", "text": question}]
    if image_bytes:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": image_data_url(image_bytes, mime_type or "image/jpeg")}
        })
    messages.append({"role": "user", "content": user_content})

    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 250
            },
            timeout=120
        )
        if response.status_code != 200:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except Exception:
                detail = response.text
            return f"API error ({response.status_code}): {detail}"
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.Timeout:
        return "The request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Connection error: {e}"
    except (KeyError, IndexError, ValueError):
        return "The AI returned an unexpected response. Please try again."

# Initialize and migrate database before querying it.
init_db()

# -------------------- SESSION STATE --------------------
if "chat_id" not in st.session_state:
    chats = list_chats()
    st.session_state.chat_id = chats[0][0] if chats else create_chat()
if "pending_image" not in st.session_state:
    st.session_state.pending_image = None
if "pending_image_type" not in st.session_state:
    st.session_state.pending_image_type = None

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("# 🏗️ CrackGPT")
    st.caption("Structural Intelligence Assistant")
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.chat_id = create_chat()
        st.session_state.pending_image = None
        st.session_state.pending_image_type = None
        st.rerun()
    st.divider()
    st.markdown("### 💬 Chat History")
    for chat_id, title, updated in list_chats():
        label = title if title and title != "New conversation" else "💬 New conversation"
        if st.button(label, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.chat_id = chat_id
            st.session_state.pending_image = None
            st.session_state.pending_image_type = None
            st.rerun()

# -------------------- MAIN CHAT --------------------
chat = get_chat(st.session_state.chat_id)
if not chat:
    st.session_state.chat_id = create_chat()
    st.rerun()
chat_id, chat_title, saved_image, saved_image_type = chat


st.title("CrackGPT")
st.subheader("Structural Intelligence Assistant")
st.write("Upload a structural image and ask a specific question about visible damage, cracks, or observations.")
st.divider()


# Image upload and persistence
uploaded = st.file_uploader("📷 Upload a structural image", type=["jpg", "jpeg", "png", "webp"], key=f"upload_{chat_id}")
if uploaded is not None:
    image_bytes = uploaded.getvalue()
    mime_type = uploaded.type or "image/jpeg"
    save_image(chat_id, image_bytes, mime_type)
    saved_image = image_bytes
    saved_image_type = mime_type
elif st.session_state.pending_image is not None:
    saved_image = st.session_state.pending_image
    saved_image_type = st.session_state.pending_image_type

if saved_image:
    try:
        st.image(saved_image, caption="Image linked to this conversation", use_container_width=True)
    except Exception:
        st.warning("The saved image could not be displayed. Please upload it again.")

# Show messages
messages = get_messages(chat_id)
for role, content in messages:
    with st.chat_message(role):
        st.markdown(content)

# Question input. No automatic assessment is generated.
question = st.chat_input("Ask CrackGPT about your image...")
if question:
    question = question.strip()
    if not question:
        st.stop()
    if not saved_image and not messages:
        st.warning("Please upload an image first, then ask your question.")
        st.stop()

    save_message(chat_id, "user", question)
    if chat_title == "New conversation":
        set_chat_title(chat_id, question)


    with st.chat_message("user"):
        st.markdown(question)


    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question..."):
            answer = ask_groq(question, saved_image, saved_image_type, messages)
        st.markdown(answer)
    save_message(chat_id, "assistant", answer)
    st.rerun()


st.divider()
st.caption("CrackGPT provides image-based structural observations and is not a substitute for professional inspection.")
