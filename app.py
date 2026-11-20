
import streamlit as st
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================================================
# CONFIGURATION
# =========================================================

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>
.stApp {
    background-color: #101114;
    color: #F2F2F2;
}

section[data-testid="stSidebar"] {
    background-color: #191A20;
}

h1, h2, h3 {
    color: #F2F2F2;
}

div[data-testid="stChatMessage"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🏗️ CrackGPT")
    st.caption("Structural Intelligence")

    st.divider()

    if st.button("＋ New conversation", use_container_width=True):

        st.session_state.messages = []
        st.session_state.uploaded_image = None
        st.session_state.image_name = None
        st.rerun()

    st.divider()

    st.markdown("### CrackGPT V8")
    st.caption("BLIP Vision-Language Model")
    st.caption("LoRA Fine-tuned")

    st.divider()

    st.markdown("### Damage Categories")

    st.markdown("""
    - Cracking
    - Spalling
    - Corrosion
    - Honeycombing / Voids
    - Exposed Reinforcement
    """)

    st.divider()

    st.caption("Ask questions one at a time.")

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None

# =========================================================
# MODEL LOADING
# =========================================================

@st.cache_resource
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
# AI RESPONSE
# =========================================================

def ask_crackgpt(image, question, processor, model):

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
            max_new_tokens=100
        )

    answer = processor.decode(
        output[0],
        skip_special_tokens=True
    )

    return answer.strip()

# =========================================================
# MAIN INTERFACE
# =========================================================

st.title("🏗️ CrackGPT")
st.caption("AI Structural Damage Assessment Assistant")

# =========================================================
# IMAGE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a structural image to start chatting",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:

    new_image = Image.open(uploaded_file).convert("RGB")

    # Reset conversation when a different image is uploaded
    if st.session_state.image_name != uploaded_file.name:

        st.session_state.uploaded_image = new_image
        st.session_state.image_name = uploaded_file.name
        st.session_state.messages = []

    st.session_state.uploaded_image = new_image

# =========================================================
# SHOW UPLOADED IMAGE
# =========================================================

if st.session_state.uploaded_image is not None:

    st.image(
        st.session_state.uploaded_image,
        caption="Structural image under analysis",
        width=500
    )

    st.success("Image loaded. Ask your first question below.")

else:

    st.info("Upload an image to begin your structural assessment conversation.")

# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# =========================================================
# CONVERSATIONAL QUESTION INPUT
# =========================================================

prompt = st.chat_input(
    "Ask CrackGPT a question about the structural damage..."
)

if prompt:

    if st.session_state.uploaded_image is None:

        st.warning("Please upload a structural image first.")

    else:

        # Display user question
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate answer
        with st.chat_message("assistant"):

            try:

                processor, model = load_crackgpt()

                with st.spinner("CrackGPT is analyzing your question..."):

                    answer = ask_crackgpt(
                        st.session_state.uploaded_image,
                        prompt,
                        processor,
                        model
                    )

                st.markdown(answer)

                # Save answer
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:

                st.error(f"Error: {str(e)}")

