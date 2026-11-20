
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="CrackGPT",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- THEME --------------------
st.markdown("""
<style>
.stApp {
    background: #212121;
    color: #ECECEC;
}

header[data-testid="stHeader"] {
    background: #212121;
}

section[data-testid="stSidebar"] {
    background: #171717;
    border-right: 1px solid #333333;
}

section[data-testid="stSidebar"] * {
    color: #ECECEC !important;
}

.block-container {
    max-width: 1050px;
    padding-top: 1.5rem;
    padding-bottom: 6rem;
}

h1, h2, h3 {
    color: #FFFFFF !important;
}

[data-testid="stChatMessage"] {
    background: transparent;
    border: none;
}

[data-testid="stChatInput"] {
    border-radius: 16px !important;
}

.stButton > button {
    border-radius: 10px;
    height: 42px;
}

div[data-testid="stFileUploader"] {
    background: #2B2B2B;
    border: 1px solid #444444;
    border-radius: 14px;
    padding: 8px;
}

footer {
    display: none;
}

/* Reduce empty space */
[data-testid="stVerticalBlock"] {
    gap: 0.8rem;
}

/* Chat text */
p {
    line-height: 1.65;
}

/* Sidebar */
.sidebar-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 5px;
}

.sidebar-subtitle {
    color: #A0A0A0;
    font-size: 14px;
}

/* Welcome screen */
.welcome {
    text-align: center;
    padding-top: 100px;
}

.welcome h1 {
    font-size: 42px;
}

.welcome-text {
    color: #AAAAAA;
    font-size: 16px;
}

/* Image preview */
.image-preview {
    border-radius: 12px;
}

/* Remove default top space */
div[data-testid="stMainBlockContainer"] {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# -------------------- SESSION STATE --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None


# -------------------- SIDEBAR --------------------
with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-title">🏗️ CrackGPT</div>
        <div class="sidebar-subtitle">Structural Damage AI</div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

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

    st.markdown(
        """
        <div style="color:#AAAAAA; font-size:14px;">
        Analyze concrete and infrastructure damage using AI.
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------- WELCOME --------------------
if not st.session_state.messages:

    st.markdown(
        """
        <div class="welcome">
            <h1>CrackGPT</h1>
            <h2 style="font-weight:400;">How can I help you today?</h2>
            <p class="welcome-text">
                Upload a structural damage image and ask CrackGPT.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# -------------------- CHAT HISTORY --------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=320)

        st.markdown(message["content"])


# -------------------- IMAGE UPLOAD --------------------
uploaded_file = st.file_uploader(
    "📎 Attach a structural damage image",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.current_image = image
    st.session_state.image_name = uploaded_file.name

    st.markdown("**Attached image**")
    st.image(image, width=260)


# -------------------- CHAT INPUT --------------------
prompt = st.chat_input("Message CrackGPT...")


if prompt:

    image_to_use = st.session_state.current_image

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "image": image_to_use
    })

    # Display user message
    with st.chat_message("user"):

        if image_to_use is not None:
            st.image(image_to_use, width=320)

        st.markdown(prompt)

    response = (
        "Your image and question have been received. "
        "The CrackGPT V8 inference integration is the next step."
    )

    with st.chat_message("assistant"):

        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()

