import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def summarize(text: str, max_retries: int = 3) -> str:
    """Send text to the LLM and return a plain-text summary, retrying on failure."""

    system_instruction = "You are a concise summarizer. Summarize the given text in 3-4 sentences, capturing only the key points."

# The for attempt in range(...) loop is the retry logic: if the API call fails (network issue, rate limit, etc.), it waits a bit and tries again, up to 3 times, before giving up.
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=text,
                config=types.GenerateContentConfig(
                    #system_instruction sets the AI's behavior separately from the actual text
                    system_instruction=system_instruction, 

                    #temperature=0.2 keeps the summary focused/consistent
                    temperature=0.2,

                    # max_output_tokens=300 caps the response length (the "tokens" concept).
                    max_output_tokens=1024,
                ),
            )
            return response.text

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2 * attempt)  # wait longer each retry: 2s, 4s, 6s...


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python summarize.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    print("Summarizing...")
    summary = summarize(text)
    print("\n=== Summary ===")
    print(summary)