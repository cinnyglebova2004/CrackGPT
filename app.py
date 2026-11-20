
import streamlit as st
from PIL import Image

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="CrackGPT | Structural AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>

/* Main application */
.stApp {
    background: #0f1117;
    color: #e8eaf0;
}

/* Header */
header[data-testid="stHeader"] {
    background: #0f1117;
}

/* Hide footer */
footer {
    display: none;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #171a21;
    border-right: 1px solid #292d36;
}

section[data-testid="stSidebar"] * {
    color: #e8eaf0;
}

section[data-testid="stSidebar"] .stButton button {
    background: #252932;
    color: #ffffff;
    border: 1px solid #363c48;
    border-radius: 10px;
    height: 45px;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: #343a46;
    border-color: #777f91;
}

/* Main container */
.block-container {
    max-width: 1000px;
    padding-top: 2rem;
    padding-bottom: 7rem;
}

/* Headings */
h1, h2, h3 {
    color: #f5f7fa !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
    padding: 1rem 0;
}

/* User message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #20242d;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 12px;
}

/* Assistant message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: transparent;
    padding: 18px 8px;
}

/* Text */
[data-testid="stMarkdownContainer"] p {
    color: #e5e7eb;
    line-height: 1.75;
}

/* Chat input container */
[data-testid="stChatInput"] {
    background: #20242d !important;
    border: 1px solid #3a404b !important;
    border-radius: 18px !important;
    padding: 10px !important;
}

/* IMPORTANT: Make typed text visible */
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background: transparent !important;
    caret-color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    font-size: 16px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #9299a6 !important;
    -webkit-text-fill-color: #9299a6 !important;
    opacity: 1 !important;
}

/* Input focus */
[data-testid="stChatInput"]:focus-within {
    border: 1px solid #6b8cff !important;
    box-shadow: 0 0 0 2px rgba(107, 140, 255, 0.12);
}

/* File upload */
[data-testid="stFileUploader"] {
    background: #1b1f27;
    border: 1px solid #343a45;
    border-radius: 14px;
    padding: 12px;
}

[data-testid="stFileUploader"] label {
    color: #e8eaf0 !important;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
    transition: 0.2s ease;
}

/* Image */
[data-testid="stImage"] img {
    border-radius: 12px;
}

/* Divider */
hr {
    border-color: #303540;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-thumb {
    background: #3b414c;
    border-radius: 10px;
}

/* Responsive */
@media (max-width: 768px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""", unsafe_allow_html=True)


# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.markdown("""
    <div style="padding:10px 0 5px 0;">
        <h2 style="margin-bottom:0;">🏗️ CrackGPT</h2>
        <p style="color:#9ca3af;margin-top:5px;">
            Structural Damage AI
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New chat", use_container_width=True):

        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.image_name = None

        st.rerun()

    st.markdown("---")

    st.markdown("""
    <div style="padding:8px 2px;">
        <h4>CrackGPT V8</h4>
        <p style="color:#9ca3af;font-size:14px;">
            AI Structural Assessment
        </p>
        <div style="
            display:inline-block;
            background:#262c36;
            padding:6px 10px;
            border-radius:8px;
            font-size:12px;
            color:#b7c5ff;">
            BLIP + LoRA
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div style="color:#9ca3af;font-size:14px;line-height:1.7;">
        Analyze structural damage in concrete and infrastructure using AI.
    </div>
    """, unsafe_allow_html=True)


# =========================
# HOME SCREEN
# =========================
if len(st.session_state.messages) == 0:

    st.markdown("""
    <div style="text-align:center;padding-top:70px;padding-bottom:30px;">

        <div style="
            font-size:48px;
            font-weight:700;
            color:#f8fafc;
            letter-spacing:-1px;">
            CrackGPT
        </div>

        <h2 style="
            font-size:30px;
            font-weight:500;
            margin-top:30px;">
            How can I help you today?
        </h2>

        <p style="
            color:#9ca3af;
            font-size:16px;
            margin-top:12px;">
            Upload a structural damage image and ask CrackGPT.
        </p>

    </div>
    """, unsafe_allow_html=True)


# =========================
# CHAT HISTORY
# =========================
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=450)

        st.markdown(message["content"])


# =========================
# IMAGE UPLOAD
# =========================
st.markdown(
    "<p style='color:#9ca3af;font-size:14px;'>"
    "📎 Attach a structural damage image"
    "</p>",
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload image",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.uploaded_image = image
    st.session_state.image_name = uploaded_file.name

    st.image(
        image,
        caption=uploaded_file.name,
        width=400
    )

else:

    if st.session_state.uploaded_image is not None:
        st.session_state.uploaded_image = None
        st.session_state.image_name = None


# =========================
# CHAT INPUT
# =========================
prompt = st.chat_input(
    "Message CrackGPT...",
    key="crackgpt_chat_input"
)


# =========================
# SEND MESSAGE
# =========================
if prompt:

    image_to_use = st.session_state.uploaded_image

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "image": image_to_use
    })

    # Display user message
    with st.chat_message("user"):

        if image_to_use is not None:
            st.image(image_to_use, width=450)

        st.markdown(prompt)

    # =========================
    # AI RESPONSE
    # =========================
    response = (
        "Your message has been received.\n\n"
        "The CrackGPT V8 BLIP + LoRA model connection "
        "will provide structural damage analysis here."
    )

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()
