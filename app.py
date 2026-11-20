
import streamlit as st
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================================================
# CONFIG
# =========================================================

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

st.set_page_config(
    page_title="CrackGPT V8",
    page_icon="🏗️",
    layout="wide"
)

# =========================================================
# UI STYLE
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
        st.session_state.assessment_started = False
        st.session_state.assessment_completed = False
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

    st.caption("AI-based preliminary structural assessment")

# =========================================================
# LOAD MODEL
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
# MODEL ANSWER
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
    ).strip()

    return answer

# =========================================================
# ASSESSMENT QUESTIONS
# =========================================================

ASSESSMENT_QUESTIONS = [
    (
        "Damage Identification",
        "What type of structural damage is visible in this image?"
    ),
    (
        "Damage Location",
        "Where is the damage located in the structural element?"
    ),
    (
        "Damage Description",
        "Describe the visible characteristics and extent of the damage."
    ),
    (
        "Severity Assessment",
        "How severe does the visible damage appear?"
    ),
    (
        "Possible Causes",
        "What are the possible causes of this damage?"
    ),
    (
        "Structural Risks",
        "What structural risks could this damage create?"
    ),
    (
        "Durability Impact",
        "How could this damage affect the long-term durability of the structure?"
    ),
    (
        "Further Investigation",
        "What additional inspections or tests are required to evaluate this damage?"
    ),
    (
        "Recommended Repair",
        "What repair or rehabilitation method may be suitable for this damage?"
    ),
    (
        "Complete Assessment",
        "Provide a complete structural damage assessment summarizing the damage, severity, causes, risks, and recommended actions."
    )
]

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "assessment_started" not in st.session_state:
    st.session_state.assessment_started = False

if "assessment_completed" not in st.session_state:
    st.session_state.assessment_completed = False

# =========================================================
# MAIN PAGE
# =========================================================

st.title("Structural Inspection Assistant")

st.caption(
    "Upload a structural damage image to begin your assessment."
)

# =========================================================
# IMAGE UPLOAD
# =========================================================

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

    if not st.session_state.assessment_started:

        if st.button(
            "Start Structural Assessment",
            type="primary",
            use_container_width=True
        ):

            st.session_state.assessment_started = True
            st.rerun()

# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================================================
# RUN SEQUENTIAL ASSESSMENT
# =========================================================

if (
    st.session_state.assessment_started
    and not st.session_state.assessment_completed
    and st.session_state.uploaded_image is not None
):

    image = st.session_state.uploaded_image

    try:

        processor, model = load_crackgpt()

        st.markdown("---")
        st.markdown("## 🏗️ CrackGPT Structural Assessment")

        progress = st.progress(0)

        status = st.empty()

        assessment_results = []

        for index, (heading, question) in enumerate(
            ASSESSMENT_QUESTIONS
        ):

            status.markdown(
                f"### Step {index + 1}/10 · {heading}"
            )

            # Display question as a conversational assistant message
            with st.chat_message("assistant"):

                st.markdown(f"**{question}**")

                with st.spinner("Analyzing image..."):

                    answer = ask_crackgpt(
                        image,
                        question,
                        processor,
                        model
                    )

                st.write(answer)

            # Save question and answer
            assessment_results.append(
                (heading, question, answer)
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**{heading}**\n\n{question}\n\n{answer}"
            })

            progress.progress(
                (index + 1) / len(ASSESSMENT_QUESTIONS)
            )

        progress.empty()
        status.empty()

        st.success("Structural assessment completed.")

        st.warning(
            "This is an AI-based preliminary visual assessment. "
            "Structural severity, safety, and repair requirements "
            "must be verified by a qualified structural engineer."
        )

        st.session_state.assessment_completed = True

    except Exception as e:

        st.error(f"Model error: {str(e)}")

# =========================================================
# FOLLOW-UP CONVERSATION
# =========================================================

if st.session_state.assessment_completed:

    prompt = st.chat_input(
        "Ask a follow-up question about the assessment..."
    )

    if prompt:

        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            try:

                processor, model = load_crackgpt()

                with st.spinner("CrackGPT is thinking..."):

                    answer = ask_crackgpt(
                        st.session_state.uploaded_image,
                        prompt,
                        processor,
                        model
                    )

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:

                st.error(f"Model error: {str(e)}")
