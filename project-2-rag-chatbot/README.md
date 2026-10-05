# 💬 CloudDesk Support Chat

A RAG-powered chatbot that answers questions grounded in CloudDesk's documentation (refund policy, pricing plans, troubleshooting guide), with citations and multi-turn memory, built with Python, LangChain, Chroma, Google Gemini, and Streamlit.

**🔗 Live demo:** [ai-journey-rag-chatbot.streamlit.app](https://ai-journey-rag-chatbot.streamlit.app)

## Problem

Support documentation is only useful if people can find the specific answer they need inside it. This app lets a user ask a plain-language question and get a direct, grounded answer, with the source documents cited, rather than searching or reading through full policy pages themselves.

## Architecture
User question
│
▼
Embed question (Gemini embedding model)
│
▼
Chroma vector store ──► top-k similar chunks (with metadata: source, chunk_id)
│
▼
Prompt = system instructions + conversation history + retrieved chunks + question
│
▼
Gemini (gemini-3.6-flash) generates a structured answer:
{ answer, sources_used }
│
▼
Streamlit chat UI displays the answer + cited sources,
and appends this turn to session history for the next question


Source documents (`docs/*.txt`) are chunked (Day 17), embedded, and persisted to a local Chroma index (Day 18) the first time the app runs; retrieval (Day 19) finds the most relevant chunks for each question.

## How it works

1. On first startup, the app checks if a vector index already exists. If not, it builds one from the documents in `docs/`.
2. A user's question is embedded and compared against every stored chunk to find the top-5 most relevant ones.
3. Those chunks, plus the conversation history so far, are sent to Gemini with instructions to answer only from the provided context.
4. The model returns a structured response: the answer text, and the specific source filenames it actually drew on, not just whatever was retrieved.
5. The Streamlit UI displays the conversation as a real chat, with sources shown under each answer, and remembers history so follow-up questions like "what about the Pro plan?" work correctly.

## Tech stack

- **Python** — core language
- **LangChain** — prompt templates, structured output, the retrieve-generate chain
- **Chroma** — local, persisted vector store
- **Google Gemini API** — embeddings (`gemini-embedding-001`) and generation (`gemini-3.6-flash`)
- **Pydantic** — structured output validation for grounded answers and cited sources
- **Streamlit** — chat UI and deployment (Streamlit Community Cloud)

## Run it locally

```bash
git clone https://github.com/ergauravsharma/ai-journey.git
cd ai-journey/project-2-rag-chatbot
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root (`ai-journey/.env`):

GOOGLE_API_KEY=your_api_key_here


Then run:
```bash
streamlit run app.py
```

The first run will take a bit longer, since it builds the vector index from `docs/` before answering any questions.

## What I'd improve

- Formal evaluation of answer quality and retrieval accuracy (planned for Week 6)
- A relevance threshold or re-ranking step to reduce irrelevant chunks being retrieved on borderline questions
- Support for uploading new documents through the UI instead of a fixed `docs/` folder
- Streaming responses so answers appear progressively instead of all at once

---

*Built as Project 2 of a 60-day journey from senior software engineer to GenAI/Agentic developer.*