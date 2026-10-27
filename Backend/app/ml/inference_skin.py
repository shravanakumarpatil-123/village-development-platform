"""
Skin Disease Inference Module
================================
Loads model_skin.joblib and runs predictions on new skin images.
Also handles:
  - Rule-based urgency classification (deterministic)
  - Claude API advice generation (fill CLAUDE_API_KEY to activate)

Used by: backend/app/routers/healthcare.py
"""

import io
import os
import json
import urllib.request
import joblib
import numpy as np
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

MODEL_PATH = r"D:\village-development-platform\ML\model_skin.joblib"

# Fill this in when you have a Claude API key
CLAUDE_API_KEY = ""

# -----------------------------------------------------------------------------
# CONDITION INFO
# Plain language descriptions shown to ASHA workers
# -----------------------------------------------------------------------------

CONDITION_INFO = {
    "eczema": {
        "display": "Eczema",
        "description": "Eczema causes dry, itchy, inflamed skin. It is not contagious and is often triggered by allergens or irritants.",
        "common": True,
    },
    "melanoma": {
        "display": "Melanoma (Possible)",
        "description": "Melanoma is a serious form of skin cancer. Irregular dark patches or moles that are changing in size or color are warning signs.",
        "common": False,
    },
    "atopic_dermatitis": {
        "display": "Atopic Dermatitis",
        "description": "Atopic dermatitis is a chronic allergic skin condition causing red, itchy patches. Very common in children.",
        "common": True,
    },
    "basal_cell_carcinoma": {
        "display": "Basal Cell Carcinoma (Possible)",
        "description": "Basal cell carcinoma is the most common type of skin cancer. It appears as a pearly or waxy bump, often on sun-exposed skin.",
        "common": False,
    },
    "melanocytic_nevi": {
        "display": "Melanocytic Nevi (Mole)",
        "description": "Common moles. Usually harmless but should be monitored for changes in size, shape, or color.",
        "common": True,
    },
    "benign_keratosis": {
        "display": "Benign Keratosis",
        "description": "A harmless scaly or warty skin growth. Usually appears with age and does not require treatment unless causing discomfort.",
        "common": True,
    },
    "psoriasis": {
        "display": "Psoriasis / Lichen Planus",
        "description": "Psoriasis causes red, scaly patches. It is a chronic condition and is not contagious. Stress and infections can trigger flares.",
        "common": True,
    },
    "seborrheic_keratosis": {
        "display": "Seborrheic Keratosis",
        "description": "Harmless growths that appear as waxy, stuck-on looking spots. Very common in older adults and not contagious.",
        "common": True,
    },
    "fungal_infection": {
        "display": "Fungal Infection (Ringworm / Tinea)",
        "description": "Fungal infections like ringworm cause ring-shaped, scaly rashes. Very common in warm humid climates. Contagious — avoid sharing towels or clothing.",
        "common": True,
    },
    "viral_infection": {
        "display": "Viral Infection (Warts / Molluscum)",
        "description": "Warts and molluscum are caused by viruses. They appear as small bumps and can spread through direct contact.",
        "common": True,
    },
}

# -----------------------------------------------------------------------------
# URGENCY RULES
# Deterministic — same condition always gives same urgency
# -----------------------------------------------------------------------------

URGENCY_RULES = {
    "eczema": {
        "level": "low",
        "label": "Low — Manage & Monitor",
        "color": "yellow",
        "action": "Keep skin moisturized. Avoid known triggers. Refer to doctor if severe or not improving in 2 weeks.",
    },
    "melanoma": {
        "level": "critical",
        "label": "Critical — Refer Immediately",
        "color": "red",
        "action": "URGENT: Refer to a dermatologist or hospital immediately. Do not delay. Early detection is critical for melanoma.",
    },
    "atopic_dermatitis": {
        "level": "low",
        "label": "Low — Manage & Monitor",
        "color": "yellow",
        "action": "Keep skin moisturized. Avoid allergens. Refer to doctor if widespread or affecting sleep.",
    },
    "basal_cell_carcinoma": {
        "level": "high",
        "label": "High — Refer to Doctor",
        "color": "red",
        "action": "Refer to doctor within 1-2 weeks. Basal cell carcinoma is treatable when caught early.",
    },
    "melanocytic_nevi": {
        "level": "routine",
        "label": "Routine — Monitor",
        "color": "green",
        "action": "Monitor for changes in size, shape, or color. Schedule routine checkup in 6-12 months.",
    },
    "benign_keratosis": {
        "level": "routine",
        "label": "Routine — No Action Needed",
        "color": "green",
        "action": "Harmless growth. No treatment needed unless causing discomfort or cosmetic concern.",
    },
    "psoriasis": {
        "level": "moderate",
        "label": "Moderate — See Doctor",
        "color": "orange",
        "action": "Refer to doctor within 1 month. Psoriasis is manageable with proper treatment.",
    },
    "seborrheic_keratosis": {
        "level": "routine",
        "label": "Routine — No Action Needed",
        "color": "green",
        "action": "Harmless growth. No treatment needed unless irritated or causing cosmetic concern.",
    },
    "fungal_infection": {
        "level": "low",
        "label": "Low — Treat & Monitor",
        "color": "yellow",
        "action": "Antifungal cream available at local pharmacy. Keep area dry and clean. Refer to doctor if not improving in 2 weeks.",
    },
    "viral_infection": {
        "level": "low",
        "label": "Low — Monitor",
        "color": "yellow",
        "action": "Many viral skin infections resolve on their own. Avoid scratching. Refer to doctor if spreading rapidly.",
    },
}

# -----------------------------------------------------------------------------
# IMAGE PREPROCESSING — must match training exactly
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
# MODEL LOADING — lazy, loaded once on first request
# -----------------------------------------------------------------------------

_model_data = None
_feature_extractor = None
_model_loaded = False


def _load_models():
    global _model_data, _feature_extractor, _model_loaded
    if _model_loaded:
        return

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Skin model not found at {MODEL_PATH}. "
            "Please run train_skin_model.py first."
        )

    print("Loading skin disease model...")
    _model_data = joblib.load(MODEL_PATH)

    print("Loading MobileNetV2 feature extractor for skin model...")
    extractor = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    extractor.classifier = torch.nn.Identity()
    for param in extractor.parameters():
        param.requires_grad = False
    extractor.eval()
    _feature_extractor = extractor
    _model_loaded = True
    print("Skin screening model ready.")


# -----------------------------------------------------------------------------
# CLAUDE API ADVICE
# -----------------------------------------------------------------------------

def _get_claude_advice(condition: str, patient_age: int = None, patient_gender: str = None) -> str:
    if not CLAUDE_API_KEY:
        return URGENCY_RULES[condition]["action"]

    info = CONDITION_INFO[condition]
    urgency = URGENCY_RULES[condition]

    patient_context = ""
    if patient_age:
        patient_context += f"Patient age: {patient_age}. "
    if patient_gender:
        patient_context += f"Gender: {patient_gender}. "

    prompt = f"""You are a rural healthcare assistant helping an ASHA worker in India.

A patient's skin photo has been analyzed and the AI detected:
- Condition: {info['display']}
- Description: {info['description']}
- Urgency: {urgency['label']}
{patient_context}

Please provide:
1. Simple explanation of the condition in plain language
2. Immediate steps the ASHA worker should take
3. Home care advice (hygiene, diet, what to avoid)
4. Warning signs that need immediate doctor visit

Keep it practical for rural India. Do NOT suggest specific prescription medicines by name.
Always end with: "This is AI-assisted screening — always consult a qualified doctor."
"""

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["content"][0]["text"]
    except Exception as e:
        print(f"Claude API failed: {e}. Using fallback advice.")
        return URGENCY_RULES[condition]["action"]


# -----------------------------------------------------------------------------
# MAIN INFERENCE FUNCTION
# -----------------------------------------------------------------------------

def predict_skin_condition(
    image_bytes: bytes,
    patient_age: int = None,
    patient_gender: str = None,
) -> dict:
    """
    Takes raw image bytes from an uploaded photo,
    returns a structured result with condition, urgency, and advice.
    """
    _load_models()

    # Preprocess image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = preprocess(img).unsqueeze(0)  # (1, 3, 224, 224)

    # Extract features
    with torch.no_grad():
        features = _feature_extractor(tensor).numpy()  # (1, 1280)

    # Predict condition
    classifier = _model_data["classifier"]
    condition = classifier.predict(features)[0]

    # Confidence
    try:
        probabilities = classifier.predict_proba(features)[0]
        confidence = float(np.max(probabilities))
        # Top 3 predictions for transparency
        classes = _model_data.get("classes", [])
        if classes:
            top3_idx = np.argsort(probabilities)[::-1][:3]
            top3 = [
                {
                    "condition": classes[i],
                    "display": CONDITION_INFO.get(classes[i], {}).get("display", classes[i]),
                    "probability": round(float(probabilities[i]) * 100, 1),
                }
                for i in top3_idx
            ]
        else:
            top3 = []
    except Exception:
        confidence = 0.6
        top3 = []

    info = CONDITION_INFO.get(condition, {
        "display": condition,
        "description": "Skin condition detected.",
        "common": True,
    })
    urgency = URGENCY_RULES.get(condition, {
        "level": "moderate",
        "label": "Moderate — See Doctor",
        "color": "orange",
        "action": "Consult a doctor for proper diagnosis.",
    })

    advice = _get_claude_advice(condition, patient_age, patient_gender)

    return {
        "condition": condition,
        "condition_display": info["display"],
        "condition_description": info["description"],
        "is_common_condition": info["common"],
        "confidence": round(confidence, 3),
        "confidence_percent": f"{round(confidence * 100, 1)}%",
        "top3_predictions": top3,
        "urgency_level": urgency["level"],
        "urgency_label": urgency["label"],
        "urgency_color": urgency["color"],
        "action": urgency["action"],
        "advice": advice,
        "disclaimer": (
            "This is AI-assisted screening for informational purposes only. "
            "It does not replace professional medical diagnosis. "
            "Always consult a qualified doctor for skin conditions."
        ),
    }
