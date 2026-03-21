import joblib
import os

MODEL_PATH = "model/email_model.pkl"
VECTORIZER_PATH = "model/vectorizer.pkl"

model = None
vectorizer = None

if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)


def predict_email(subject, sender, body):

    if model is None or vectorizer is None:
        return "general"

    text = f"{subject} {sender} {body}"
    X = vectorizer.transform([text])

    return model.predict(X)[0]


def predict_with_confidence(subject, sender, body):

    if model is None or vectorizer is None:
        return "general", 0.5

    text = f"{subject} {sender} {body}"
    X = vectorizer.transform([text])

    probs = model.predict_proba(X)[0]
    pred = model.classes_[probs.argmax()]

    return pred, max(probs)
