# 🎫 Support Ticket Triage

An AI-powered app that classifies customer support tickets (category, priority, sentiment) and drafts a reply — built with Python, LangChain, Google Gemini, and Streamlit.

**🔗 Live demo:** [gaurav-triage.streamlit.app](https://gaurav-triage.streamlit.app)

<!-- ![Demo](demo.gif) -->
   *(Demo GIF coming soon — see the [live app](https://gaurav-triage.streamlit.app) to try it yourself)*

## Problem

Support teams spend significant time manually reading, categorizing, and prioritizing incoming tickets before they can even start responding. This app automates the first pass: given raw ticket text, it instantly classifies the ticket and drafts a starting-point reply, so a human agent can review and send rather than starting from scratch.

## How it works

1. User pastes ticket text into the app.
2. The text is sent to Google's Gemini model via a LangChain chain (prompt template → structured LLM output).
3. The model returns a validated (pydantic) structured result: category, priority, sentiment, confidence score, and a draft reply.
4. Results are displayed instantly in the UI — low-confidence classifications are flagged for human review.

## Tech stack

- **Python** — core language
- **LangChain** — prompt templates, structured output chains
- **Google Gemini API** — the underlying LLM (`gemini-3.6-flash`)
- **Pydantic** — schema validation for structured LLM output
- **Streamlit** — UI and deployment (Streamlit Community Cloud)

## Run it locally

```bash
git clone https://github.com/ergauravsharma/ai-journey.git
cd ai-journey
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
GOOGLE_API_KEY=your_api_key_here

Then run:
```bash
streamlit run app.py
```

## What I'd improve

- Add streaming responses so the draft reply appears progressively instead of all at once
- Support batch triage (upload a CSV of tickets, get results for all of them)
- Add a feedback mechanism so agents can correct misclassifications, building a dataset for future fine-tuning
- Add automated evaluation (planned for Week 6 of this project)

---

*Built as Project 1 of a 60-day journey from senior software engineer to GenAI/Agentic developer.*