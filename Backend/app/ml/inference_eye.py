"""
Eye Screening Inference Module
================================
Loads the trained model_eye.joblib and runs predictions on new retinal images.
Also handles:
  - Rule-based urgency classification (deterministic, no ML needed)
  - Claude API advice generation (fill in CLAUDE_API_KEY to activate)

Used by: backend/app/routers/healthcare.py
"""

import io
import os
import json
import urllib.request
import urllib.error
import joblib
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

from app.config import settings

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# Path to the trained model file.
# Adjust this if you move model_eye.joblib somewhere else.
MODEL_PATH = r"D:\village-development-platform\ML\model_eye.joblib"

# Secure API key loaded from a local .env or OS environment.
# Keep this value out of source control.
GROQ_API_KEY = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")

# -----------------------------------------------------------------------------
# GRADE INFORMATION
# Plain language descriptions shown to ASHA workers
# -----------------------------------------------------------------------------

GRADE_INFO = {
    0: {
        "name": "No Diabetic Retinopathy",
        "short": "Healthy",
        "description": "No signs of diabetic retinopathy detected. The retina appears healthy.",
    },
    1: {
        "name": "Mild DR",
        "short": "Mild",
        "description": "Mild diabetic retinopathy detected. Small microaneurysms (tiny bulges in blood vessels) are present.",
    },
    2: {
        "name": "Moderate DR",
        "short": "Moderate",
        "description": "Moderate diabetic retinopathy. More blood vessel damage visible. Blood vessels may be blocked.",
    },
    3: {
        "name": "Severe DR",
        "short": "Severe",
        "description": "Severe diabetic retinopathy. Many blocked blood vessels. The eye is growing new vessels to compensate.",
    },
    4: {
        "name": "Proliferative DR",
        "short": "Critical",
        "description": "Proliferative (most advanced) diabetic retinopathy. Abnormal new blood vessels have grown. High risk of blindness.",
    },
}

# -----------------------------------------------------------------------------
# URGENCY RULES
# Deterministic — same grade always gives same urgency.
# No ML needed here, this is pure business logic.
# -----------------------------------------------------------------------------

URGENCY_RULES = {
    0: {
        "level": "routine",
        "label": "Routine",
        "color": "green",
        "action": "No immediate action needed. Schedule routine eye checkup in 12 months. Encourage blood sugar control.",
    },
    1: {
        "level": "low",
        "label": "Low Priority",
        "color": "yellow",
        "action": "Schedule eye examination within 6 months. Focus on blood sugar and blood pressure control.",
    },
    2: {
        "level": "moderate",
        "label": "Moderate — See Doctor",
        "color": "orange",
        "action": "Refer to eye doctor within 3 months. Do not delay. Blood sugar control is critical.",
    },
    3: {
        "level": "high",
        "label": "High — Urgent Referral",
        "color": "red",
        "action": "Refer to ophthalmologist within 2 weeks. This is serious. Patient must not miss this appointment.",
    },
    4: {
        "level": "critical",
        "label": "Critical — Immediate",
        "color": "red",
        "action": "URGENT: Refer to ophthalmologist immediately. Risk of permanent vision loss. Do not wait.",
    },
}

# -----------------------------------------------------------------------------
# IMAGE PREPROCESSING
# Must match exactly what was used during training
# -----------------------------------------------------------------------------

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# -----------------------------------------------------------------------------
# MODEL LOADING
# Loaded once when the module is first imported, then reused for every request.
# Loading is slow (~2 seconds) so we do it once at startup, not per request.
# -----------------------------------------------------------------------------

_model_data = None
_feature_extractor = None


def _load_models():
    """Loads the joblib model and MobileNetV2 feature extractor into memory."""
    global _model_data, _feature_extractor

    if _model_data is not None:
        return  # Already loaded, skip

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please run train_eye_model.py first."
        )

    print("Loading eye screening model...")
    _model_data = joblib.load(MODEL_PATH)

    print("Loading MobileNetV2 feature extractor...")
    extractor = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    extractor.classifier = torch.nn.Identity()
    for param in extractor.parameters():
        param.requires_grad = False
    extractor.eval()
    _feature_extractor = extractor
    print("Eye screening models ready.")


# -----------------------------------------------------------------------------
# AI ADVICE
# Calls Groq to generate personalized advice based on the patient's grade.
# Only runs if GROQ_API_KEY is set.
# Falls back to the hardcoded action text if key is missing or API fails.
# -----------------------------------------------------------------------------

def _get_ai_advice(grade: int, patient_age: int = None, patient_gender: str = None) -> str:
    """
    Calls the Groq API to generate personalized healthcare advice.
    Returns hardcoded advice if the API key is not set.
    """
    if not GROQ_API_KEY:
        return URGENCY_RULES[grade]["action"]

    grade_info = GRADE_INFO[grade]
    urgency = URGENCY_RULES[grade]

    patient_context = ""
    if patient_age:
        patient_context += f"Patient age: {patient_age}. "
    if patient_gender:
        patient_context += f"Gender: {patient_gender}. "

    prompt = f"""You are a rural healthcare assistant helping an ASHA worker in India.

A patient has been screened for diabetic retinopathy and the result is:
- Grade: {grade} out of 4
- Diagnosis: {grade_info['name']}
- Description: {grade_info['description']}
- Urgency: {urgency['label']}
{patient_context}

Please provide:
1. A simple explanation of what this means (in plain language an ASHA worker can explain to a patient)
2. Immediate steps the ASHA worker should take
3. Lifestyle advice for the patient (diet, blood sugar control, exercise)
4. Warning signs to watch for before the next appointment

Keep it concise, practical, and appropriate for rural India.
Do NOT suggest specific prescription medicines by name.
Always end with a reminder to consult a qualified doctor.

IMPORTANT: Add this disclaimer at the end:
"⚠️ This is AI-generated guidance for informational purposes only. Always consult a qualified doctor before making any medical decisions."
"""

    try:
        payload = json.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"Groq API call failed: {e}. Falling back to hardcoded advice.")
        return URGENCY_RULES[grade]["action"]


# -----------------------------------------------------------------------------
# MAIN INFERENCE FUNCTION
# Called by the FastAPI endpoint with raw image bytes
# -----------------------------------------------------------------------------

def predict_eye_screening(
    image_bytes: bytes,
    patient_age: int = None,
    patient_gender: str = None,
) -> dict:
    """
    Takes raw image bytes (from an uploaded file),
    runs the full inference pipeline,
    and returns a structured result dict.

    Args:
        image_bytes: Raw bytes of the uploaded retinal image
        patient_age: Optional patient age for personalized advice
        patient_gender: Optional patient gender for personalized advice

    Returns:
        {
            "grade": 0-4,
            "grade_name": "No DR" / "Mild" / etc,
            "grade_description": "...",
            "confidence": 0.0-1.0,
            "urgency_level": "routine" / "low" / "moderate" / "high" / "critical",
            "urgency_label": "Routine" / "Low Priority" / etc,
            "urgency_color": "green" / "yellow" / "orange" / "red",
            "action": "What the ASHA worker should do",
            "advice": "Detailed AI-generated or hardcoded advice",
            "disclaimer": "Always consult a qualified doctor..."
        }
    """
    # Load models if not already loaded
    _load_models()

    # Step 1: Open image from bytes
    # io.BytesIO wraps raw bytes so Pillow can read them like a file
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Step 2: Preprocess — resize + normalize
    tensor = preprocess(img)

    # Step 3: Add batch dimension
    # MobileNetV2 expects shape (batch_size, 3, 224, 224)
    # Our single image is (3, 224, 224) — unsqueeze adds the batch dim
    tensor = tensor.unsqueeze(0)  # → (1, 3, 224, 224)

    # Step 4: Extract 1280 features using MobileNetV2
    with torch.no_grad():
        features = _feature_extractor(tensor).numpy()  # shape: (1, 1280)

    # Step 5: Predict grade using the ensemble classifier
    classifier = _model_data["classifier"]
    grade = int(classifier.predict(features)[0])

    # Step 6: Get confidence score
    # predict_proba returns probability for each class [0,1,2,3,4]
    # We take the probability of the predicted class as confidence
    probabilities = classifier.predict_proba(features)[0]
    confidence = float(np.max(probabilities))

    # Step 7: Get grade info and urgency (deterministic rules)
    grade_info = GRADE_INFO[grade]
    urgency = URGENCY_RULES[grade]

    # Step 8: Get advice from Groq or fallback to deterministic medical guidance
    advice = _get_ai_advice(grade, patient_age, patient_gender)

    return {
        "grade": grade,
        "grade_name": grade_info["name"],
        "grade_short": grade_info["short"],
        "grade_description": grade_info["description"],
        "confidence": round(confidence, 3),
        "confidence_percent": f"{round(confidence * 100, 1)}%",
        "urgency_level": urgency["level"],
        "urgency_label": urgency["label"],
        "urgency_color": urgency["color"],
        "action": urgency["action"],
        "advice": advice,
        "disclaimer": (
            "This is AI-assisted screening for informational purposes only. "
            "It does not replace a professional medical diagnosis. "
            "Always consult a qualified ophthalmologist for medical decisions."
        ),
    }
