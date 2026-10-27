import importlib
import os


os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
os.environ.setdefault("SECRET_KEY", "test-secret")


def test_groq_api_is_used_for_advice(monkeypatch):
    import app.ml.inference_eye as inference_eye

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    importlib.reload(inference_eye)

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"Groq advice"}}]}'

    def fake_urlopen(req, timeout=15):
        captured["url"] = req.full_url
        captured["headers"] = req.headers
        return FakeResponse()

    monkeypatch.setattr(inference_eye.urllib.request, "urlopen", fake_urlopen)

    advice = inference_eye._get_ai_advice(1, patient_age=45, patient_gender="female")

    assert advice == "Groq advice"
    assert "api.groq.com" in captured["url"]
    assert "Authorization" in captured["headers"]
