import joblib
import os
from functools import lru_cache

MODEL_PATH = "model/email_model.pkl"
VECTORIZER_PATH = "model/vectorizer.pkl"


# -------------------------------
# LOAD MODEL (LAZY + CACHED)
# -------------------------------
@lru_cache()
def load_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        return model, vectorizer
    return None, None


# -------------------------------
# PREDICT
# -------------------------------
def predict_email(subject, sender, body):

    model, vectorizer = load_model()

    if model is None or vectorizer is None:
        return "general"

    text = f"{subject} {sender} {body}"
    X = vectorizer.transform([text])

    return model.predict(X)[0]


# -------------------------------
# CONFIDENCE
# -------------------------------
def predict_with_confidence(subject, sender, body):

    model, vectorizer = load_model()

    if model is None or vectorizer is None:
        return "general", 0.5

    text = f"{subject} {sender} {body}"
    X = vectorizer.transform([text])

    probs = model.predict_proba(X)[0]
    pred = model.classes_[probs.argmax()]

    return pred, max(probs)
