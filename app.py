
    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.3},
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


st.title("🏗️ CrackGPT")
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
