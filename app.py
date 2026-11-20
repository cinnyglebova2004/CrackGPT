
import streamlit as st
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel
from huggingface_hub import login
import io

# ================= CONFIG =================
st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_REPO = "Cinny2004/CrackGPT-V8-LoRA"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ================= PROFESSIONAL CSS =================
st.markdown("""
<style>
.stApp {
    background: #0e1117;
    color: #e8edf5;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

section[data-testid="stSidebar"] {
    background: #151a23;
    border-right: 1px solid #252e3b;
}

section[data-testid="stSidebar"] * {
    color: #e8edf5;
}

h1, h2, h3 {
    color: #f5f7fb !important;
}

p, label, span {
    color: inherit;
}

.stTextInput input,
.stTextArea textarea,
[data-testid="stChatInput"] textarea {
    color: #ffffff !important;
    background-color: #1b2330 !important;
    border: 1px solid #394657 !important;
    border-radius: 12px !important;
}

[data-testid="stChatInput"] {
    background: #151b24 !important;
    border: 1px solid #344152 !important;
    border-radius: 16px !important;
}

[data-testid="stChatInput"] textarea {
    color: white !important;
    caret-color: white !important;
}

[data-testid="stFileUploader"] {
    background: #171e28;
    border: 1px solid #344152;
    padding: 14px;
    border-radius: 14px;
}

[data-testid="stChatMessage"] {
    background: #151c26;
    border: 1px solid #283444;
    border-radius: 16px;
    padding: 15px;
    margin-bottom: 12px;
}

.stButton button {
    border-radius: 10px;
    font-weight: 600;
}

div[data-testid="stMarkdownContainer"] {
    color: #e8edf5;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)

# ================= MODEL LOADING =================
@st.cache_resource
def load_model():

    token = st.secrets["HF_TOKEN"]

    login(token=token, add_to_git_credential=False)

    processor = BlipProcessor.from_pretrained(
        BASE_MODEL,
        token=token
    )

    base_model = BlipForQuestionAnswering.from_pretrained(
        BASE_MODEL,
        token=token
    )

    model = PeftModel.from_pretrained(
        base_model,
        LORA_REPO,
        token=token
    )

    model.eval()
    model.to(DEVICE)

    return processor, model


# ================= SESSION STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_image" not in st.session_state:
    st.session_state.current_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None


# ================= SIDEBAR =================
with st.sidebar:

    st.markdown("""
    <div style="padding:10px 0;">
        <h2>🏗️ CrackGPT</h2>
        <p style="color:#9ba8b8;">Structural Intelligence</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### CrackGPT V8")
    st.caption("AI Structural Damage Assessment")
    st.caption("BLIP + LoRA Fine-tuned Model")

    st.markdown("---")

    st.markdown("### Model")
    st.markdown("🧠 BLIP VQA")
    st.markdown("⚙️ LoRA Fine-tuning")
    st.markdown(f"💻 Device: {DEVICE.upper()}")

    st.markdown("---")

    if st.button("＋ New conversation", use_container_width=True):

        st.session_state.messages = []
        st.session_state.current_image = None
        st.session_state.image_name = None
        st.rerun()

    st.markdown("""
    <div style="margin-top:20px;color:#8491a3;font-size:13px;">
        Analyze cracks, concrete defects and structural damage
        using AI-powered visual assessment.
    </div>
    """, unsafe_allow_html=True)


# ================= HEADER =================
st.markdown("""
<div style="text-align:center;padding:20px 0 10px 0;">
    <h1 style="font-size:42px;">CrackGPT</h1>
    <p style="font-size:17px;color:#9ba8b8;">
        AI-powered Structural Damage Assessment
    </p>
</div>
""", unsafe_allow_html=True)


# ================= INITIAL SCREEN =================
if len(st.session_state.messages) == 0:

    st.markdown("""
    <div style="
        text-align:center;
        padding:25px;
        background:#151c26;
        border:1px solid #283444;
        border-radius:18px;
        margin-bottom:20px;
    ">
        <h2>Structural Inspection Assistant</h2>
        <p style="color:#aab6c5;">
        Upload an image of structural damage and ask a question.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ================= IMAGE UPLOAD =================
uploaded_file = st.file_uploader(
    "📷 Upload a structural damage image",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.current_image = image
    st.session_state.image_name = uploaded_file.name

    st.markdown("### Uploaded image")

    st.image(
        image,
        caption=uploaded_file.name,
        use_container_width=True
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


# ================= INFERENCE =================
if prompt:

    current_image = st.session_state.current_image

    if current_image is None:

        st.warning("Please upload a structural damage image first.")

    else:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "image": current_image
        })

        with st.chat_message("user"):

            st.image(current_image, width=400)
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("Analyzing structural damage..."):

                try:

                    processor, model = load_model()

                    inputs = processor(
                        images=current_image,
                        text=prompt,
                        return_tensors="pt"
                    )

                    inputs = {
                        k: v.to(DEVICE)
                        for k, v in inputs.items()
                    }

                    with torch.no_grad():

                        output = model.generate(
                            **inputs,
                            max_new_tokens=100
                        )

                    answer = processor.decode(
                        output[0],
                        skip_special_tokens=True
                    )

                    st.markdown("### 🔍 Damage Assessment")
                    st.markdown(answer)

                except Exception as e:

                    answer = f"Model error: {str(e)}"

                    st.error(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        st.rerun()


# ================= FOOTER =================
st.markdown("""
<div style="
    text-align:center;
    padding:25px 0;
    color:#7f8b9c;
    font-size:12px;
">
    CrackGPT V8 · BLIP + LoRA · AI Structural Damage Assessment
</div>
""", unsafe_allow_html=True)
