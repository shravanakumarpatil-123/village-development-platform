"""
Loads the trained model and predicts a department for a new complaint.
Used by app/routers/community.py when someone submits a complaint.
"""
import os
import joblib

HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(HERE, "department_classifier.joblib")

_model = None


def _load_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "No trained model found. Run 'python ml/train_department_classifier.py' first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_department(complaint_text: str) -> str:
    model = _load_model()
    return model.predict([complaint_text])[0]
