import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma  # the vector store that saves embeddings to disk
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # wraps Gemini's embedding model for LangChain
from chunk_docs import DOCS_DIR, load_documents, chunk_documents  # reuse yesterday's loader and splitter

load_dotenv()

# Where Chroma will save its files on disk, so the index survives between runs
PERSIST_DIR = Path(__file__).parent / "chroma_db"


def build_index():
    """Load the docs, chunk them, embed each chunk, and save the result to disk."""

    # Step 1: reuse Day 17's code to load and split the documents
    docs = load_documents(DOCS_DIR)
    chunks = chunk_documents(docs)
    print(f"Loaded {len(docs)} documents, produced {len(chunks)} chunks")

    # Step 2: the embedding model that turns each chunk's text into a vector.
    # This is the same idea as Day 16's get_embedding(), but wrapped so Chroma can call it directly
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )

    # Step 3: pull out just the text and the metadata (source, chunk_id) for each chunk,
    # since Chroma expects these as two separate lists in the same order
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [{"source": chunk["source"], "chunk_id": chunk["chunk_id"]} for chunk in chunks]

    # Step 4: embed every chunk and save the result to PERSIST_DIR.
    # This is the slow, one-time step — after this, the index can be loaded instantly
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=str(PERSIST_DIR),
    )

    print(f"Index built and saved to {PERSIST_DIR}")
    return vector_store


if __name__ == "__main__":
    build_index()