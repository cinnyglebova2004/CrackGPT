import streamlit as st
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================
# CONFIGURATION
# =========================

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

st.set_page_config(
    page_title="CrackGPT V8",
    page_icon="🏗️",
    layout="wide"
)

# =========================
# UI
# =========================

st.markdown("""
<style>
.stApp {
    background-color: #101114;
    color: #f5f5f5;
}
section[data-testid="stSidebar"] {
    background-color: #191a20;
}
h1, h2, h3 {
    color: #f3f4f6;
}
div[data-testid="stChatMessage"] {
    background-color: #191a20;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.markdown("## 🏗️ CrackGPT")
    st.caption("Structural Intelligence")

    st.divider()

    if st.button("＋ New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.uploaded_image = None
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
    - Voids / Honeycombing
    - Exposed Reinforcement
    """)

    st.divider()

    st.caption("AI-based preliminary structural assessment")

# =========================
# MODEL
# =========================

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


# =========================
# INFERENCE
# =========================

def ask_model(image, question, processor, model):

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


# =========================
# STRUCTURED ASSESSMENT
# =========================

def generate_assessment(image, processor, model):

    questions = {
        "Damage Type":
            "What type of structural damage is visible in this image?",

        "Damage Location":
            "Where is the visible damage located in the structure?",

        "Severity":
            "Describe the visible extent and severity of the structural damage.",

        "Possible Causes":
            "What are the possible causes of this visible concrete damage?",

        "Structural Risks":
            "What structural risks could be associated with this damage?",

        "Recommended Action":
            "What inspection or repair action is recommended for this damage?"
    }

    results = {}

    progress = st.progress(0)

    for i, (heading, question) in enumerate(questions.items()):

        answer = ask_model(
            image,
            question,
            processor,
            model
        )

        results[heading] = answer

        progress.progress(
            (i + 1) / len(questions)
        )

    progress.empty()

    return results


# =========================
# MAIN PAGE
# =========================

st.title("Structural Inspection Assistant")

st.caption(
    "Upload a damage image and ask CrackGPT to analyze the structure."
)

# =========================
# SESSION STATE
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

# =========================
# IMAGE UPLOAD
# =========================

uploaded_file = st.file_uploader(
    "Upload a concrete or infrastructure image",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    st.session_state.uploaded_image = image

    st.image(
        image,
        caption="Uploaded structural image",
        use_container_width=True
    )

# =========================
# DISPLAY CHAT HISTORY
# =========================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# =========================
# CHAT INPUT
# =========================

prompt = st.chat_input(
    "Ask CrackGPT about the structural damage..."
)

if prompt:

    if st.session_state.uploaded_image is None:

        st.warning("Please upload a structural image first.")

    else:

        image = st.session_state.uploaded_image

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("CrackGPT is analyzing the structure..."):

                try:

                    processor, model = load_crackgpt()

                    assessment = generate_assessment(
                        image,
                        processor,
                        model
                    )

                    st.markdown("## 🏗️ Structural Damage Assessment")

                    for heading, answer in assessment.items():

                        st.markdown(
                            f"### {heading}"
                        )

                        st.write(answer)

                    st.divider()

                    st.caption(
                        "⚠️ This is an AI-based preliminary visual assessment. "
                        "Severity, structural safety, and repair requirements "
                        "must be verified through an on-site inspection "
                        "by a qualified structural engineer."
                    )

                    # Save assessment to chat history

                    formatted_response = (
                        "## 🏗️ Structural Damage Assessment\n\n"
                    )

                    for heading, answer in assessment.items():

                        formatted_response += (
                            f"### {heading}\n"
                            f"{answer}\n\n"
                        )

                    formatted_response += (
                        "---\n"
                        "⚠️ AI-based preliminary visual assessment. "
                        "On-site verification by a qualified structural engineer is required."
                    )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": formatted_response
                    })

                except Exception as e:

                    st.error(
                        f"Model error: {str(e)}"
                    )
