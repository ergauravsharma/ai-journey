import os
from dotenv import load_dotenv
from google import genai
import numpy as np

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def get_embedding(text: str) -> list[float]:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return result.embeddings[0].values


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


if __name__ == "__main__":
    sentences = [
        "The cat sat on the mat.",
        "A feline rested on the rug.",
        "I love eating pizza on weekends.",
    ]

    embeddings = [get_embedding(s) for s in sentences]

    print("Comparing sentence similarities:\n")
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            print(f'"{sentences[i]}"\nvs\n"{sentences[j]}"\nSimilarity: {sim:.4f}\n')