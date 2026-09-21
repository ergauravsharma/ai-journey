import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


class Summary(BaseModel):
    title: str
    bullets: list[str]
    sentiment: str  # "positive", "neutral", or "negative"


def summarize_structured(text: str, max_retries: int = 3) -> Summary:
    """Send text to the LLM and return a validated Summary object."""

    system_instruction = (
        "You are a summarizer. Given a text, return a JSON object with: "
        "'title' (a short headline), 'bullets' (exactly 3 key points as a list of strings), "
        "and 'sentiment' (one of: positive, neutral, negative)."
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                    response_schema=Summary,
                ),
            )
            # response.parsed gives us an already-validated pydantic object
            return response.parsed

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python structured_summarize.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    print("Summarizing...")
    result = summarize_structured(text)

    print("\n=== Structured Summary ===")
    print(f"Title: {result.title}")
    print("Bullets:")
    for b in result.bullets:
        print(f"  - {b}")
    print(f"Sentiment: {result.sentiment}")