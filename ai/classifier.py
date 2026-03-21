import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import os

MODEL_DIR = "model_bert"

tokenizer = None
model = None

if os.path.exists(MODEL_DIR):
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()


def rule_override(subject, sender, body):
    s = sender.lower()
    text = (subject + " " + body).lower()

    if "github" in s:
        return "notification"

    if "unsubscribe" in text:
        return "newsletter"

    if any(w in text for w in ["internship", "hiring", "apply"]):
        return "job_alert"

    return None


def predict_with_confidence(subject, sender, body):

    if model is None:
        return "general", 0.5

    text = f"{subject} {sender} {body}"

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0]
    pred_id = torch.argmax(probs).item()

    confidence = probs[pred_id].item()

    label = model.config.id2label[pred_id]

    # apply rule only if strong
    rule = rule_override(subject, sender, body)
    if rule:
        return rule, 0.95

    return label, confidence


def predict_email(subject, sender, body):
    label, _ = predict_with_confidence(subject, sender, body)
    return label