import os
import sys
import time
from enum import Enum
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


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


def triage(ticket_text: str, max_retries: int = 5) -> TriageResult:
    """Classify a support ticket and draft a reply, with validation and retry."""

    system_instruction = (
        "You are an experienced customer support triage specialist. Given a support ticket, "
        "you will analyze it carefully, then produce a JSON object with:\n\n"
        "- 'category': one of billing, technical, general, complaint\n"
        "- 'priority': one of low, medium, high, urgent — based on business impact and urgency of language\n"
        "- 'sentiment': one of positive, neutral, negative\n"
        "- 'confidence': a number 0.0-1.0 for how certain you are of the classification\n"
        "- 'draft_reply': a short, professional, empathetic draft reply to the customer "
        "(2-4 sentences), acknowledging their issue and stating next steps. Do not make "
        "promises you can't verify (e.g., exact refund timelines) — keep it general but reassuring.\n\n"
        "First think through what the customer actually needs, then produce the JSON."
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f'"""{ticket_text}"""',
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=1536,
                    response_mime_type="application/json",
                    response_schema=TriageResult,
                ),
            )
            return response.parsed

        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                wait_time = 25
            elif "UNAVAILABLE" in str(e):
                wait_time = 10 * attempt  # 10s, 20s, 30s... give overloaded servers time to recover
            else:
                wait_time = 2 * attempt
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            print(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)


def print_result(ticket_num: int, result: TriageResult):
    print(f"\n--- Ticket {ticket_num} ---")
    print(f"Category:   {result.category.value}")
    print(f"Priority:   {result.priority.value}")
    print(f"Sentiment:  {result.sentiment.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Draft Reply: {result.draft_reply}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python triage.py <ticket_file1> <ticket_file2> ...")
        sys.exit(1)

    for i, file_path in enumerate(sys.argv[1:], start=1):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        result = triage(text)
        print_result(i, result)
        if i < len(sys.argv[1:]):
            time.sleep(13)  # stay under the 5-requests-per-minute free tier limit