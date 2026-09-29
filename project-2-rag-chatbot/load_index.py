import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

PERSIST_DIR = Path(__file__).parent / "chroma_db"


def load_index():
    """Load an already-built index from disk, without re-embedding anything."""

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )

    # No .from_texts() here, no re-embedding — this just opens the folder Day 18 saved
    vector_store = Chroma(
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
    )

    return vector_store


if __name__ == "__main__":
    vector_store = load_index()

    # get() with no arguments returns everything stored in the index
    result = vector_store.get()
    print(f"Loaded index containing {len(result['ids'])} chunks")

    # Show the source of each chunk, so we can confirm all three documents made it in
    sources = [meta["source"] for meta in result["metadatas"]]
    print("Sources present:", set(sources))