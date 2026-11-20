
def save_msg(cid, role, content):
    now=datetime.now().isoformat(timespec="seconds")
    c=db(); c.execute("INSERT INTO messages(chat_id,role,content,created) VALUES(?,?,?,?)",(cid,role,content,now)); c.execute("UPDATE chats SET updated=? WHERE id=?",(now,cid)); c.commit(); c.close()

def messages(cid):
    c=db(); rows=c.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id",(cid,)).fetchall(); c.close(); return rows

def set_title(cid, title):
    c=db(); c.execute("UPDATE chats SET title=? WHERE id=? AND title='New conversation'",(title[:55],cid)); c.commit(); c.close()

def data_url(data, mime):
    return "data:"+(mime or "image/jpeg")+";base64,"+base64.b64encode(data).decode()

def ask_ai(question, img, mime, history):
    key=st.secrets.get("GROQ_API_KEY","")
    model=st.secrets.get("GROQ_MODEL",DEFAULT_MODEL)
    if not key: return "Missing GROQ_API_KEY. Add it in Streamlit app Secrets."
    msgs=[{"role":"system","content":SYSTEM_PROMPT}]
    for role,txt in history[-16:]:
        if role in ("user","assistant"): msgs.append({"role":role,"content":txt})
    content=[{"type":"text","text":question}]
    if img: content.append({"type":"image_url","image_url":{"url":data_url(img,mime)}})
    msgs.append({"role":"user","content":content})
    try:
        r=requests.post(GROQ_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model,"messages":msgs,"temperature":0.2,"max_tokens":650},timeout=90)
        if not r.ok:
            try: detail=r.json().get("error",{}).get("message",r.text)
            except Exception: detail=r.text
            return f"Groq API error ({r.status_code}): {detail}"
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.Timeout: return "The request timed out. Please try again."
    except requests.RequestException as e: return f"Connection error: {e}"
    except (KeyError,IndexError,TypeError): return "Unexpected response from AI service. Please retry."

# Sidebar
with st.sidebar:
    st.markdown("# 🏗️ CrackGPT")
    st.caption("Structural Intelligence")
    if st.button("＋ New conversation", use_container_width=True):
        st.session_state.chat_id = create_chat()
        st.session_state.upload_mode = True
        st.rerun()
    st.divider()
    st.markdown("### Your conversations")
    for cid, title, updated in chats():
        if st.button(title or "New conversation", key=f"chat_{cid}", use_container_width=True):
            st.session_state.chat_id = cid
            st.session_state.upload_mode = False
            st.rerun()
    st.divider()
    st.markdown("### CrackGPT Vision")
    st.caption("Image-based structural damage discussion")
    st.caption("Conversational question-by-question assessment")

# Select active conversation
if "chat_id" not in st.session_state or not chat(st.session_state.chat_id):
    st.session_state.chat_id = create_chat()
    st.session_state.upload_mode = True
chat_id = st.session_state.chat_id
active = chat(chat_id)

st.title("🏗️ CrackGPT")
st.caption("Structural damage discussion, one question at a time")

# Image upload or stored image
stored_img = active[2]
stored_mime = active[3] or "image/jpeg"
if stored_img:
    st.image(stored_img, caption="Image attached to this conversation", width=520)
    if st.button("Replace image"):
        st.session_state.upload_mode = True
if not stored_img or st.session_state.get("upload_mode", False):
    upload = st.file_uploader("Upload structural damage image", type=["jpg", "jpeg", "png", "webp"], key=f"upload_{chat_id}")
    if upload:
        img_bytes = upload.getvalue()
        save_image(chat_id, img_bytes, upload.type or "image/jpeg")
        st.session_state.upload_mode = False
        st.rerun()

# Display chat history
for role, content in messages(chat_id):
    with st.chat_message(role):
        st.markdown(content)


prompt = st.chat_input("Ask a question about the uploaded damage image...")
if prompt:
    if not stored_img:
        st.warning("Upload an image first, then ask your question.")
    else:
        save_msg(chat_id, "user", prompt)
        history = messages(chat_id)[:-1]
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question..."):
                answer = ask_ai(prompt, stored_img, stored_mime, history)
            st.markdown(answer)
        save_msg(chat_id, "assistant", answer)
        if active[1] == "New conversation":
            set_title(chat_id, prompt)
        st.rerun()
