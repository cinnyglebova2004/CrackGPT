import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="CrackGPT",
    page_icon="🏗️",
    layout="wide"
)

# Dark ChatGPT-style theme
st.markdown("""
<style>
.stApp {
    background-color: #212121;
    color: #ffffff;
}
section[data-testid="stSidebar"] {
    background-color: #171717;
}
div[data-testid="stChatInput"] {
    background-color: #303030;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🏗️ CrackGPT")
    st.caption("Structural Damage AI")

    if st.button("＋ New chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.rerun()

    st.divider()
    st.markdown("### CrackGPT V8")
    st.caption("AI Structural Damage Assessment")
    st.caption("BLIP + LoRA")

# Initialize chat
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# Main screen
st.title("CrackGPT")

if not st.session_state.messages:
    st.markdown(
        "<div style='text-align:center; padding-top:100px;'>"
        "<h2>How can I help you today?</h2>"
        "<p>Upload a structural damage image and ask CrackGPT.</p>"
        "</div>",
        unsafe_allow_html=True
    )

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

        if msg.get("image"):
            st.image(msg["image"], width=400)

# Upload image
uploaded_file = st.file_uploader(
    "Attach an image",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.session_state.uploaded_image = image

    st.image(
        image,
        caption="Uploaded structural image",
        width=350
    )

# Chat input
prompt = st.chat_input("Message CrackGPT...")

if prompt:

    user_message = {
        "role": "user",
        "content": prompt
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        if st.session_state.uploaded_image is not None:
            st.write(
                "Image received! CrackGPT V8 interface is ready. "
                "The trained model connection will be configured next."
            )
        else:
            st.write(
                "Hello! I'm CrackGPT, your structural damage assessment "
                "assistant. Upload an image of concrete damage and ask me "
                "a question."
            )

    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Image received! CrackGPT V8 interface is ready. "
            "The trained model connection will be configured next."
        )
    })

    st.rerun()
