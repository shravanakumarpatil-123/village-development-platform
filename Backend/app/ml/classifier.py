"""
Complaint → Department inference.

Loads the trained model (model_complaint.joblib) if it exists.
Falls back to keyword heuristics if no model has been trained yet.

Used by: app/routers/community.py when a complaint is submitted.
"""

import os
from typing import Tuple

import joblib

from app.models import Department

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_complaint.joblib")

_model_data = None
_model_loaded = False

# ---------------------------------------------------------------------------
# Keyword fallback — used before any model is trained
# ---------------------------------------------------------------------------

_KEYWORDS = {
    Department.road: ["road", "pothole", "bridge", "street", "tar", "highway", "path"],
    Department.water: ["water", "handpump", "borewell", "pipeline", "tank", "drinking", "supply"],
    Department.electricity: ["power", "electricity", "transformer", "streetlight", "street light", "current", "pole", "light"],
    Department.sanitation: ["garbage", "sewage", "drain", "toilet", "waste", "mosquito", "trash", "clean"],
    Department.health: ["hospital", "doctor", "medicine", "ambulance", "health", "vaccination", "dengue", "clinic"],
    Department.education: ["school", "teacher", "student", "textbook", "classroom", "midday meal", "college"],
    Department.agriculture: ["crop", "fertilizer", "seed", "irrigation", "farmer", "soil", "pesticide", "harvest"],
}


def _keyword_fallback(text: str) -> Tuple[Department, float]:
    text_lower = text.lower()
    for department, keywords in _KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return department, 0.4  # low confidence — keyword match
    return Department.other, 0.3


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _load_model():
    global _model_data, _model_loaded
    if not _model_loaded:
        if os.path.exists(MODEL_PATH):
            print("Loading complaint classifier model...")
            _model_data = joblib.load(MODEL_PATH)
            print("Complaint classifier ready.")
        _model_loaded = True
    return _model_data


# ---------------------------------------------------------------------------
# Main inference function
# ---------------------------------------------------------------------------

def predict_department(text: str) -> Tuple[Department, float]:
    """
    Predicts the government department for a complaint.
    Returns (department, confidence) where confidence is in [0, 1].

    Uses trained ML model if available, keyword heuristic otherwise.
    """
    model_data = _load_model()

    if model_data is None:
        # No trained model yet — use keyword fallback
        return _keyword_fallback(text)

    tfidf = model_data["tfidf"]
    classifier = model_data["classifier"]

    # Transform text using the same TF-IDF fitted during training
    features = tfidf.transform([text])

    # Predict department
    prediction = classifier.predict(features)[0]

    # Get confidence from probability
    try:
        probabilities = classifier.predict_proba(features)[0]
        confidence = float(max(probabilities))
    except Exception:
        confidence = 0.6  # fallback if predict_proba not available

    # Map string prediction to Department enum
    try:
        department = Department(prediction.lower())
    except ValueError:
        department = Department.other

    return department, round(confidence, 3)
