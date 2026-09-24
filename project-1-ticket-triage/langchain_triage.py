import os
import sys
from enum import Enum
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

load_dotenv()

class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"
    COMPLAINT = "complaint"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    sentiment: Sentiment
    confidence: float
    draft_reply: str


# --- Step 1: The LLM, wrapped by LangChain ---
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.2,
    max_output_tokens=1536,
    google_api_key=os.environ["GOOGLE_API_KEY"],
)


# --- Step 2: Bind the LLM to our schema (LangChain's version of response_schema) ---
structured_llm = llm.with_structured_output(TriageResult)

# --- Step 3: A reusable prompt template ---
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an experienced customer support triage specialist. Given a support ticket, "
     "analyze it carefully, then classify it and draft a reply.\n\n"
     "- 'category': one of billing, technical, general, complaint\n"
     "- 'priority': one of low, medium, high, urgent\n"
     "- 'sentiment': one of positive, neutral, negative\n"
     "- 'confidence': a number 0.0-1.0\n"
          "- 'draft_reply': a short, professional, empathetic reply (2-4 sentences). "
     "Do not promise specific amounts, dates, or timelines you can't verify — keep it "
     "general but reassuring.\n\n"
     "First think through what the customer needs, then produce the result."),
    ("user", "{ticket_text}"),
])

# --- Step 4: The chain — prompt piped into the structured LLM ---
chain = prompt | structured_llm


def triage(ticket_text: str) -> TriageResult:
    return chain.invoke({"ticket_text": ticket_text})


def print_result(result: TriageResult):
    print(f"Category:   {result.category.value}")
    print(f"Priority:   {result.priority.value}")
    print(f"Sentiment:  {result.sentiment.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Draft Reply: {result.draft_reply}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python langchain_triage.py <ticket_file>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    print("Triaging...")
    result = triage(text)
    print_result(result)