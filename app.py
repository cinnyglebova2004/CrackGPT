import streamlit as st
import torch
import requests
import base64
from io import BytesIO
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================================================
# CONFIGURATION
# =========================================================

BASE_MODEL = "Salesforce/blip-vqa-base"
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

GROQ_MODEL = "qwen/qwen3.8-27b"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

# =========================================================
# STYLING
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
# SYSTEM INSTRUCTIONS
# =========================================================

SYSTEM_PROMPT = """
You are CrackGPT, an AI assistant specializing in preliminary
visual assessment of structural damage in concrete and infrastructure.

You are having a real conversation with the user.

RULES:

1. Answer ONLY the question the user currently asks.
2. Do not automatically generate a complete report.
3. Keep answers clear, natural, and conversational.
4. Use the uploaded image as your primary visual evidence.
5. Identify visible damage carefully. Possible damage includes:
   cracking, spalling, corrosion, honeycombing, voids,
   exposed reinforcement, delamination, leakage, deformation,
   and other deterioration.
6. Never invent damage that is not visually supported.
7. Do not blindly trust the BLIP/V8 model observation.
   It may be incorrect, repetitive, or nonsensical.
8. Independently inspect the image and use the V8 output only
   as an additional clue.
9. Clearly distinguish visible observations from possible causes.
10. Do not claim exact severity or structural safety from an
    image alone.
11. When discussing causes, use terms such as "may be caused by"
    or "possible causes include" where appropriate.
12. Give practical inspection and repair suggestions when asked.
13. Do not repeat the same damage label as an answer to every
    question.
14. Remember previous conversation messages and use them when
    relevant to the user's follow-up questions.
15. Use simple engineering language. Avoid meaningless answers.
16. If the image is unclear, explicitly state the limitation.

Your responses should be helpful, technically responsible,
and easy for civil engineering students and engineers to understand.
"""

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

    st.markdown("### Reasoning Engine")
    st.caption("Qwen Vision + Engineering Reasoning")

    st.divider()

    st.markdown("### Damage Categories")

    st.markdown("""
    - Cracking
    - Spalling
    - Corrosion
    - Honeycombing / Voids
    - Exposed Reinforcement
    - Delamination
    """)

    st.divider()

    st.caption("AI-based preliminary structural assessment")

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
# LOAD V8 MODEL
# =========================================================

@st.cache_resource
def load_crackgpt_v8():

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
# V8 VISUAL OBSERVATION
# =========================================================

def get_v8_observation(image, question, processor, model):

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
            max_new_tokens=60
        )

    observation = processor.decode(
        output[0],
        skip_special_tokens=True
    ).strip()

    return observation

# =========================================================
# IMAGE ENCODING FOR VISION REASONING
# =========================================================

def image_to_base64(image):

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=85
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/jpeg;base64,{encoded}"

# =========================================================
# CONVERSATIONAL REASONING
# =========================================================

def get_reasoning_answer(
    question,
    image,
    v8_observation,
    conversation_history
):

    api_key = st.secrets["GROQ_API_KEY"]

    image_data = image_to_base64(image)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Previous conversation
    for message in conversation_history:

        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    # Current question + image + V8 clue
    current_content = [
        {
            "type": "text",
            "text": (
                f"User's current question: {question}\n\n"
                f"CrackGPT V8 visual model observation: "
                f"{v8_observation}\n\n"
                "Treat the V8 observation as potentially unreliable. "
                "Inspect the image independently and answer the user's "
                "current question using visible evidence. Do not merely "
                "repeat the V8 observation."
            )
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_data
            }
        }
    ]

    messages.append({
        "role": "user",
        "content": current_content
    })

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        },
        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    answer = result["choices"][0]["message"]["content"]

    return answer.strip()

# =========================================================
# MAIN PAGE
# =========================================================

st.title("🏗️ CrackGPT")
st.caption("AI Structural Damage Assessment Assistant")

# =========================================================
# IMAGE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a structural damage image",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:

    new_image = Image.open(
        uploaded_file
    ).convert("RGB")

    if st.session_state.image_name != uploaded_file.name:

        st.session_state.uploaded_image = new_image
        st.session_state.image_name = uploaded_file.name
        st.session_state.messages = []

    st.session_state.uploaded_image = new_image

# =========================================================
# DISPLAY IMAGE
# =========================================================

if st.session_state.uploaded_image is not None:

    st.image(
        st.session_state.uploaded_image,
        caption="Image analyzed by CrackGPT",
        width=500
    )

else:

    st.info("Upload a structural image to begin.")

# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input(
    "Ask CrackGPT about the structural damage..."
)

if prompt:

    if st.session_state.uploaded_image is None:

        st.warning("Please upload an image first.")

    else:

        image = st.session_state.uploaded_image

        # Display user question
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            try:

                # Load V8 visual model
                with st.spinner("Examining image with CrackGPT V8..."):

                    processor, v8_model = load_crackgpt_v8()

                    v8_observation = get_v8_observation(
                        image,
                        prompt,
                        processor,
                        v8_model
                    )

                # Generate reasoning response
                with st.spinner("Engineering reasoning in progress..."):

                    answer = get_reasoning_answer(
                        question=prompt,
                        image=image,
                        v8_observation=v8_observation,
                        conversation_history=st.session_state.messages[:-1]
                    )

                st.markdown(answer)

                # Save assistant answer
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            except requests.exceptions.HTTPError as e:

                st.error(
                    f"Reasoning API error: {e.response.text}"
                )

            except Exception as e:

                st.error(f"CrackGPT error: {str(e)}")
