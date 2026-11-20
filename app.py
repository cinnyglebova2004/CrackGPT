
import streamlit as st
from PIL import Image

# ================= CONFIG =================
st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS =================
st.markdown("""
<style>

/* Main application */
.stApp {
    background-color: #111827;
    color: #F9FAFB;
}

/* Header */
header[data-testid="stHeader"] {
    background: #111827;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0B1120;
    border-right: 1px solid #263247;
}

section[data-testid="stSidebar"] * {
    color: #E5E7EB;
}

/* Main layout */
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Headings */
h1, h2, h3 {
    color: #F9FAFB !important;
}

/* Paragraphs */
p, label {
    color: #D1D5DB;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background-color: #1B2433;
    border: 1px solid #263247;
    border-radius: 14px;
    padding: 16px;
}

/* Chat input */
[data-testid="stChatInput"] {
    background-color: #FFFFFF !important;
    border: 2px solid #64748B !important;
    border-radius: 14px !important;
}

[data-testid="stChatInput"] textarea {
    color: #111827 !important;
    background-color: #FFFFFF !important;
    caret-color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #6B7280 !important;
    opacity: 1 !important;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background-color: #1B2433;
    border: 1px solid #374151;
    border-radius: 14px;
    padding: 14px;
}

[data-testid="stFileUploader"] * {
    color: #E5E7EB !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid #374151;
    font-weight: 600;
}

/* Image */
img {
    border-radius: 12px;
}

/* Hide footer */
footer {
    visibility: hidden;
}

/* Remove unnecessary top whitespace */
[data-testid="stVerticalBlock"] {
    gap: 1rem;
}

</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None


# ================= SIDEBAR =================
with st.sidebar:

    st.markdown("# 🏗️ CrackGPT")

    st.markdown("### Structural Intelligence")

    st.caption("AI-powered infrastructure damage assessment")

    st.divider()

    if st.button("＋  New Analysis", use_container_width=True):

        st.session_state.messages = []
        st.session_state.current_image = None
        st.session_state.image_name = None

        st.rerun()

    st.divider()

    st.markdown("### MODEL")

    st.markdown("**CrackGPT V8**")

    st.caption("BLIP Vision-Language Model")

    st.caption("LoRA Fine-Tuned")

    st.divider()

    st.markdown("### Supported Analysis")

    st.markdown("""
    - Concrete cracking
    - Spalling
    - Corrosion
    - Honeycombing
    - Exposed reinforcement
    - Surface damage
    """)

    st.divider()

    st.caption("Structural damage analysis powered by AI.")


# ================= MAIN HEADER =================
if len(st.session_state.messages) == 0:

    st.markdown(
        """
        <div style="text-align:center; padding-top:45px;">
            <div style="
                font-size:15px;
                color:#60A5FA;
                letter-spacing:3px;
                font-weight:600;
            ">
                STRUCTURAL INTELLIGENCE
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.title("CrackGPT")

    st.markdown(
        """
        <div style="
            font-size:28px;
            font-weight:400;
            color:#F9FAFB;
            margin-bottom:10px;
        ">
        Structural Damage Assessment
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "Analyze concrete and infrastructure images using an AI vision model."
    )

else:

    st.markdown("## CrackGPT")
    st.caption("Structural Damage Assessment")


# ================= IMAGE UPLOAD =================
st.markdown("### 📷 Upload Structural Image")

uploaded_file = st.file_uploader(
    "Upload an image for inspection",
    type=["jpg", "jpeg", "png", "webp"],
    label_visibility="collapsed"
)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.current_image = image
    st.session_state.image_name = uploaded_file.name

    st.success(f"Image loaded: {uploaded_file.name}")

    st.image(
        image,
        caption="Uploaded structural image",
        width=500
    )

elif st.session_state.current_image is not None:

    st.image(
        st.session_state.current_image,
        caption="Current image",
        width=500
    )


# ================= CHAT HISTORY =================
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=400)

        st.markdown(message["content"])


# ================= CHAT INPUT =================
prompt = st.chat_input(
    "Describe the damage or ask a question about the image..."
)

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

    # Temporary response until model connection is implemented
    response = """
### Analysis Request Received

Your image and question have been received successfully.

**CrackGPT V8 Integration**
The trained BLIP + LoRA damage assessment model will provide the actual structural damage analysis once the model inference pipeline is connected to this interface.
"""

    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()
