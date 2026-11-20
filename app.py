
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="CrackGPT",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- CSS ----------
st.markdown("""
<style>
.stApp {
    background: #212121;
    color: #ececec;
}

header[data-testid="stHeader"] {
    background: #212121;
}

section[data-testid="stSidebar"] {
    background: #171717;
    border-right: 1px solid #303030;
}

section[data-testid="stSidebar"] * {
    color: #ececec !important;
}

.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

h1, h2, h3 {
    color: #f5f5f5 !important;
}

[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
}

[data-testid="stChatInput"] {
    background: #2f2f2f !important;
    border: 1px solid #444 !important;
    border-radius: 18px !important;
}

[data-testid="stFileUploader"] {
    background: #2f2f2f;
    border: 1px solid #444;
    border-radius: 14px;
    padding: 10px;
}

.stButton button {
    border-radius: 10px;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:

    st.markdown("""
    <h2 style="margin-bottom:0;">🏗️ CrackGPT</h2>
    <p style="color:#9b9b9b;">Structural Damage AI</p>
    """, unsafe_allow_html=True)

    if st.button("＋ New chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.current_image = None
        st.session_state.image_name = None
        st.rerun()

    st.markdown("---")

    st.markdown("### CrackGPT V8")
    st.caption("AI Structural Damage Assessment")
    st.caption("BLIP + LoRA")

    st.markdown("---")

    st.caption("Analyze concrete and infrastructure damage using AI.")

# ---------- SESSION STATE ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None

# ---------- MAIN ----------
if len(st.session_state.messages) == 0:

    st.markdown(
        """
        <div style="text-align:center; padding-top:100px;">
            <h1 style="font-size:42px;">CrackGPT</h1>
            <h2 style="font-weight:400;">
                How can I help you today?
            </h2>
            <p style="color:#a0a0a0;">
                Upload a structural damage image and ask a question.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        "<h2 style='text-align:center;'>CrackGPT</h2>",
        unsafe_allow_html=True
    )

# ---------- CHAT HISTORY ----------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=450)

        st.markdown(message["content"])

# ---------- IMAGE UPLOAD ----------
uploaded_file = st.file_uploader(
    "📎 Upload a structural image",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="visible"
)

if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.current_image = image
    st.session_state.image_name = uploaded_file.name

    st.image(
        image,
        caption=uploaded_file.name,
        width=400
    )

# ---------- CHAT INPUT ----------
prompt = st.chat_input("Message CrackGPT...")

if prompt:

    image_to_use = st.session_state.current_image

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "image": image_to_use
    })

    with st.chat_message("user"):

        if image_to_use is not None:
            st.image(image_to_use, width=400)

        st.markdown(prompt)

    # Placeholder until actual V8 model is connected
    response = (
        "Your message has been received. The CrackGPT V8 model "
        "connection is being configured. Actual AI damage analysis "
        "will be available once the trained BLIP + LoRA model is connected."
    )

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()

