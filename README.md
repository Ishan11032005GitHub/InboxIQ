# InboxIQ

An intelligent email assistant that classifies, prioritizes, and generates replies using a hybrid ML + rule-based system.

## Features

- Gmail integration (OAuth2)
- Email classification (TF-IDF + Logistic Regression)
- Confidence scoring
- Smart rule overrides
- AI reply generation (Gemini API)
- Feedback-driven retraining
- Email scheduling

## Tech Stack

- Python
- Streamlit
- Scikit-learn
- Google Gmail API
- Gemini API

## Architecture

User → Streamlit UI → Gmail API  
                         ↓  
             ML Classifier + Rules  
                         ↓  
             AI Reply Generator  

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
