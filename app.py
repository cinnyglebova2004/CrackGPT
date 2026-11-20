
import streamlit as st
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =========================================================
# UI STYLING
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #111318;
    color: #E8EAF0;
}

header[data-testid="stHeader"] {
    background-color: #111318;
}

.block-container {
    max-width: 1000px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}

section[data-testid="stSidebar"] {
    background-color: #17191E;
    border-right: 1px solid #2A2D35;
}

h1, h2, h3 {
    color: #F5F5F5 !important;
}

p, label {
    color: #D5D8DE;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 14px;
    padding: 12px;
}

/* Chat input */
[data-testid="stChatInput"] {
    background-color: #24262C !important;
    border: 1px solid #444751 !important;
    border-radius: 16px !important;
}

[data-testid="stChatInput"] textarea {
    color: #FFFFFF !important;
    background-color: transparent !important;
    caret-color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 16px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #A7ABB5 !important;
    -webkit-text-fill-color: #A7ABB5 !important;
    opacity: 1 !important;
}

/* Upload section */
[data-testid="stFileUploader"] {
    background-color: #1B1D23;
    border: 1px solid #343740;
    border-radius: 14px;
    padding: 12px;
}

[data-testid="stFileUploader"] * {
    color: #E5E7EB !important;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
}

/* Images */
img {
    border-radius: 12px;
}

/* Hide footer */
footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# MODEL LOADING
# =========================================================
@st.cache_resource(show_spinner=False)
def load_crackgpt():

    token = st.secrets["HF_TOKEN"]

    processor = BlipProcessor.from_pretrained(
        BASE_MODEL
    )

    base_model = BlipForQuestionAnswering.from_pretrained(
        BASE_MODEL
    )

    model = PeftModel.from_pretrained(
        base_model,
        LORA_MODEL,
        token=token
    )

    model.to(DEVICE)
    model.eval()

    return processor, model


# =========================================================
# INFERENCE
# =========================================================
def predict_damage(image, question):

    processor, model = load_crackgpt()

    inputs = processor(
        images=image,
        text=question,
        return_tensors="pt"
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():

        output = model.generate(
            **inputs,
            max_new_tokens=80
        )

    answer = processor.decode(
        output[0],
        skip_special_tokens=True
    )

    return answer.strip()


# =========================================================
# SESSION STATE
# =========================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "uploaded_image_name" not in st.session_state:
    st.session_state.uploaded_image_name = None


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.markdown("# 🏗️ CrackGPT")
    st.caption("Structural Intelligence")

    st.divider()

    if st.button("＋ New conversation", use_container_width=True):

        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.uploaded_image_name = None

        st.rerun()

    st.divider()

    st.markdown("### CrackGPT V8")
    st.caption("BLIP Vision-Language Model")
    st.caption("LoRA Fine-tuned")

    st.divider()

    st.markdown("### Damage categories")

    st.markdown("""
    - Cracking
    - Spalling
    - Corrosion
    - Honeycombing
    - Exposed reinforcement
    - Surface defects
    """)

    st.divider()

    st.caption("AI-assisted structural damage assessment")


# =========================================================
# HEADER
# =========================================================
st.markdown(
    "<h1 style='text-align:center;'>CrackGPT</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align:center;color:#9CA3AF;'>"
    "AI-Powered Structural Damage Assessment"
    "</p>",
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# EMPTY CHAT SCREEN
# =========================================================
if not st.session_state.messages:

    st.markdown(
        "<h2 style='text-align:center;margin-top:50px;'>"
        "Structural Inspection Assistant"
        "</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center;color:#9CA3AF;'>"
        "Upload a damage image and ask a question to begin."
        "</p>",
        unsafe_allow_html=True
    )


# =========================================================
# IMAGE UPLOAD
# =========================================================
st.markdown("### 📎 Structural Image")

uploaded_file = st.file_uploader(
    "Upload a concrete or infrastructure image",
    type=["jpg", "jpeg", "png", "webp"],
    key="image_upload"
)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.uploaded_image = image
    st.session_state.uploaded_image_name = uploaded_file.name

elif st.session_state.uploaded_image is not None:

    image = st.session_state.uploaded_image


# Display current image
if st.session_state.uploaded_image is not None:

    st.image(
        st.session_state.uploaded_image,
        caption=st.session_state.uploaded_image_name,
        width=450
    )


# =========================================================
# CHAT HISTORY
# =========================================================
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message.get("image") is not None:
            st.image(message["image"], width=400)

        st.markdown(message["content"])


# =========================================================
# CHAT INPUT
# =========================================================
prompt = st.chat_input(
    "Ask CrackGPT about the structural damage..."
)


# =========================================================
# PROCESS QUESTION
# =========================================================
if prompt:

    if st.session_state.uploaded_image is None:

        st.warning("Please upload a structural image before asking a question.")

    else:

        current_image = st.session_state.uploaded_image

        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "image": current_image
        })

        # Display user message
        with st.chat_message("user"):

            st.image(current_image, width=400)
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):

            with st.spinner("CrackGPT is analyzing the image..."):

                try:

                    answer = predict_damage(
                        current_image,
                        prompt
                    )

                    st.markdown(answer)

                except Exception as error:

                    answer = (
                        "I couldn't complete the analysis.\n\n"
                        f"**Error:** `{str(error)}`"
                    )

                    st.error(answer)

        # Save assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()


# =========================================================
# FOOTER
# =========================================================
st.divider()

st.caption(
    "CrackGPT V8 | BLIP + LoRA | AI Structural Assessment"
)
