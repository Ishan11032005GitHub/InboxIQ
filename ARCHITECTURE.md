# ARCHITECTURE

                ┌────────────────────┐
                │ Streamlit UI │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Google OAuth2 │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Gmail API │
                └─────────┬──────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ Email Processing Pipeline │
        │ │
        │ 1. Rule Engine │
        │ 2. ML Classifier (TF-IDF + LR) │
        │ 3. Confidence Scoring │
        │ 4. Priority Assignment │
        └──────────────┬──────────────────┘
                       │
                       ▼
        ┌────────────────────────────┐
        │ Gemini Reply Generator │
        └──────────────┬─────────────┘
                       │
                       ▼
        ┌────────────────────────────┐
        │ Feedback Loop + Retraining │
        └────────────────────────────┘
