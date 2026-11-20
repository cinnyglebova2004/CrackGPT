
import streamlit as st
import torch
import requests
import base64

from io import BytesIO
from PIL import Image
from transformers import BlipProcessor, BlipForQuestionAnswering
from peft import PeftModel

# =========================================================
# 1. CONFIGURATION
# =========================================================

BASE_MODEL = "Salesforce/blip-vqa-base"

# Correct repository name from your Hugging Face screenshot
LORA_MODEL = "Cinny2004/CrackGPT-V8-LoRA"

# Vision-capable Groq model
GROQ_MODEL = ""qwen/qwen3.8-27b""

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

st.set_page_config(
    page_title="CrackGPT | Structural Intelligence",
    page_icon="🏗️",
    layout="wide"
)

# =========================================================
# 2. UI STYLING
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #101114;
    color: #f2f2f2;
}

section[data-testid="stSidebar"] {
    background-color: #191a20;
}

h1, h2, h3 {
    color: #f2f2f2;
}

.stChatMessage {
    border-radius: 12px;
}

div[data-testid="stChatInput"] {
    background-color: #24252b;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are CrackGPT, a conversational AI assistant specialized in
preliminary visual structural damage assessment.

Your domain includes:
- Concrete structures
- Buildings
- Bridges
- Columns
- Beams
- Slabs
- Structural walls
- Roads and infrastructure
- Steel structural components

You can identify and discuss:
- Cracking
- Spalling
- Corrosion
- Honeycombing
- Surface voids
- Exposed reinforcement
- Delamination
- Leakage
- Deformation
- Other visible deterioration

CONVERSATION RULES:

1. Answer the user's current question directly.
2. Do not automatically produce all 10 assessment answers.
3. Respond naturally like a conversational assistant.
4. Remember the previous conversation and use it when relevant.
5. Use the uploaded image as visual context.
6. Do not blindly trust the V8 model output.
7. Independently inspect the image and use the V8 prediction only as
   an additional clue.
8. Do not repeatedly answer "spalling" to unrelated questions.
9. Never invent structural damage that is not visible.
10. Clearly separate visible observations from possible causes.
11. If uncertain, explain what cannot be confirmed from the image.
12. Explain structural concepts in simple engineering language.
13. When asked about severity, explain the reasons for your assessment.
14. When asked about causes, give possible causes rather than claiming
    certainty.
15. When asked about repairs, give practical engineering recommendations.
16. Do not claim a structure is safe or unsafe from an image alone.
17. Recommend professional inspection when necessary.

Answer in a clear, useful, technically responsible manner.
"""

# =========================================================
# 4. SIDEBAR
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

    st.markdown("### AI Reasoning")
    st.caption("Vision + Engineering Interpretation")

    st.divider()

    st.markdown("### Damage Categories")

    st.markdown("""
    - Cracking
    - Spalling
    - Corrosion
    - Honeycombing
    - Surface voids
    - Exposed reinforcement
    - Delamination
    """)

    st.divider()

    st.caption("Preliminary AI structural assessment")

# =========================================================
# 5. SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "image_name" not in st.session_state:
    st.session_state.image_name = None

# =========================================================
# 6. LOAD V8 MODEL
# =========================================================

@st.cache_resource
def load_crackgpt_v8():

    hf_token = st.secrets["HF_TOKEN"]

    processor = BlipProcessor.from_pretrained(
        BASE_MODEL
    )

    base_model = BlipForQuestionAnswering.from_pretrained(
        BASE_MODEL
    )

    model = PeftModel.from_pretrained(
        base_model,
        LORA_MODEL,
        token=hf_token
    )

    model.to(DEVICE)
    model.eval()

    return processor, model

# =========================================================
# 7. V8 VISUAL ANALYSIS
# =========================================================

def analyze_with_v8(image, question, processor, model):

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

        outputs = model.generate(
            **inputs,
            max_new_tokens=60
        )

    answer = processor.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return answer.strip()

# =========================================================
# 8. IMAGE CONVERSION
# =========================================================

def encode_image(image):

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
# 9. REASONING MODEL
# =========================================================

def ask_reasoning_ai(
    question,
    image,
    v8_observation,
    conversation_history
):

    groq_key = st.secrets["GROQ_API_KEY"]

    image_url = encode_image(image)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Include previous conversational messages
    for message in conversation_history:

        messages.append({
            "role": message["role"],
            "content": message["content"]
        })

    # Current question with image and V8 observation
    user_content = [
        {
            "type": "text",
            "text": (
                "CURRENT USER QUESTION:\n"
                + question
                + "\n\nV8 VISUAL MODEL OBSERVATION:\n"
                + v8_observation
                + "\n\nIndependently inspect the attached image. "
                "The V8 observation may be incorrect. "
                "Answer the current question directly, using "
                "visual evidence and engineering reasoning."
            )
        },
        {
            "type": "image_url",
            "image_url": {
                "url": image_url
            }
        }
    ]

    messages.append({
        "role": "user",
        "content": user_content
    })

    # Groq API
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {groq_key}",
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
# 10. MAIN INTERFACE
# =========================================================

st.title("🏗️ CrackGPT Structural Assessment")

st.caption(
    "Upload an image and start a conversation about structural damage."
)

# =========================================================
# 11. IMAGE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a structural damage image",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:

    new_image = Image.open(
        uploaded_file
    ).convert("RGB")

    # Reset history when a new image is uploaded
    if st.session_state.image_name != uploaded_file.name:

        st.session_state.uploaded_image = new_image
        st.session_state.image_name = uploaded_file.name
        st.session_state.messages = []

    st.session_state.uploaded_image = new_image

# =========================================================
# 12. DISPLAY IMAGE
# =========================================================

if st.session_state.uploaded_image is not None:

    st.image(
        st.session_state.uploaded_image,
        caption="Image analyzed by CrackGPT",
        width=500
    )

    st.success(
        "Image loaded. Ask your first question below."
    )

else:

    st.info(
        "Upload an image to begin your structural assessment."
    )

# =========================================================
# 13. DISPLAY CONVERSATION
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# =========================================================
# 14. CHAT INPUT
# =========================================================

prompt = st.chat_input(
    "Ask CrackGPT about the structural damage..."
)

if prompt:

    if st.session_state.uploaded_image is None:

        st.warning("Please upload an image first.")

    else:

        current_image = st.session_state.uploaded_image

        # Save and display user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            try:

                # -----------------------------
                # V8 VISUAL ANALYSIS
                # -----------------------------

                with st.spinner(
                    "CrackGPT V8 is examining the image..."
 
                ):

                    processor, v8_model = load_crackgpt_v8()

                    v8_observation = analyze_with_v8(
                        current_image,
                        prompt,
                        processor,
                        v8_model
                    )

                # -----------------------------
                # REASONING
                # -----------------------------

                with st.spinner(
                    "Preparing engineering response..."
                ):

                    answer = ask_reasoning_ai(
                        question=prompt,
                        image=current_image,
                        v8_observation=v8_observation,
                        conversation_history=st.session_state.messages[:-1]
                    )

                # Display final answer
                st.markdown(answer)

                # Save assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            # -----------------------------
            # ERROR HANDLING
            # -----------------------------

            except requests.exceptions.HTTPError as e:

                st.error(
                    f"Groq API error: {e.response.text}"
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The AI request timed out. Please try again."
                )

            except Exception as e:

                st.error(
                    f"CrackGPT error: {str(e)}"
                )
