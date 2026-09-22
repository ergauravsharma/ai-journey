import os
import sys
import time
from enum import Enum
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"
    COMPLAINT = "complaint"


class Classification(BaseModel):
    category: Category
    confidence: float  # 0.0 to 1.0
    reasoning: str


def classify(text: str, max_retries: int = 3) -> Classification:
    """Classify text into a fixed category, with validation and retry."""

    system_instruction = (
        "You are a support ticket classifier. Classify the given text into exactly one of these "
        "categories: billing, technical, general, complaint.\n\n"
        "Return a JSON object with:\n"
        "- 'category': one of the exact category values above\n"
        "- 'confidence': a number from 0.0 to 1.0 indicating how certain you are\n"
        "- 'reasoning': one short sentence explaining why you chose this category\n\n"
        "If the text is ambiguous, choose the closest matching category and reflect your "
        "uncertainty in the confidence score."
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f'"""{text}"""',
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                    response_schema=Classification,
                ),
            )
            return response.parsed

        except ValidationError as e:
            print(f"Attempt {attempt}: model output didn't match schema — {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python classify.py <text_file>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    print("Classifying...")
    result = classify(text)

    print("\n=== Classification ===")
    print(f"Category: {result.category.value}")
    print(f"Confidence: {result.confidence}")
    print(f"Reasoning: {result.reasoning}")