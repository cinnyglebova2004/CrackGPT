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
    st.divider()
    st.markdown("### Topics")
    st.caption("Cracking · Spalling · Corrosion · Honeycombing · Voids · Delamination")
    st.divider()
    st.caption("Preliminary visual assessment only")

# ===================== IMAGE / HEADER =====================
st.title("🏗️ CrackGPT Structural Assessment")
st.caption("Upload an image once, then ask questions one at a time. Your conversation is saved in this chat link.")
image_name, image_blob, image_mime = chat[2], chat[3], chat[4]
upload = st.file_uploader("Upload a structural damage image", type=["jpg","jpeg","png","webp"])
if upload is not None:
    if upload.name != image_name:
        save_image(chat_id, upload)
        st.rerun()
if image_blob:
    try:
        image = Image.open(BytesIO(image_blob)).convert("RGB")
        st.image(image, caption="Image attached to this conversation", width=560)
    except Exception:
        image = None
else:
    image = None
    st.info("Upload an image to begin.")

# ===================== CHAT HISTORY =====================
messages = get_messages(chat_id)
for m in messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ===================== GROQ CALL =====================
def image_data_url(blob, mime):
    encoded = base64.b64encode(blob).decode("utf-8")
    return f"data:{mime or 'image/jpeg'};base64,{encoded}"


def groq_answer(question, image_blob, image_mime, history):
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing in Streamlit Secrets.")
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Send conversational text history, excluding the just-added current question.
    for m in history:
        api_messages.append({"role": m["role"], "content": m["content"]})
    current_content = [{"type": "text", "text": question}]
    if image_blob:
        current_content.append({"type": "image_url", "image_url": {"url": image_data_url(image_blob, image_mime)}})
    api_messages.append({"role": "user", "content": current_content})
    resp = requests.post(API_URL, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={"model": GROQ_MODEL, "messages": api_messages, "temperature": 0.25, "max_tokens": 1200}, timeout=120)
    if not resp.ok:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Groq API ({resp.status_code}): {detail}")
    return resp.json()["choices"][0]["message"]["content"].strip()


# ===================== INPUT =====================
question = st.chat_input("Ask CrackGPT about the structural damage…")
if question:
    if not image_blob:
        st.warning("Please upload an image first.")
    else:
        save_message(chat_id, "user", question)
        update_title(chat_id, question)
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Examining the image and preparing an engineering answer…"):
                try:
                    # Reload current DB messages; remove current question from history to avoid duplication.
                    prior = get_messages(chat_id)[:-1]
                    answer = groq_answer(question, image_blob, image_mime, prior)
                    st.markdown(answer)
                    save_message(chat_id, "assistant", answer)
                except Exception as e:
                    st.error(str(e))
