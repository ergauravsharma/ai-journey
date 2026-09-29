import sys
from load_index import load_index  # reuse Day 18's function to open the saved Chroma index


def retrieve(question: str, k: int = 3) -> list:
    """Embed a question and return the top-k most relevant chunks from the vector store."""

    vector_store = load_index()  # opens chroma_db/ without re-embedding anything

    # similarity_search embeds the question internally, then finds the k closest
    # stored chunks by comparing embeddings, same idea as Day 16's cosine similarity
    results = vector_store.similarity_search(question, k=k)

    return results


def print_results(question: str, results: list):
    print(f'Question: "{question}"\n')
    for i, doc in enumerate(results, start=1):
        # doc.page_content is the chunk's text, doc.metadata is the {source, chunk_id} we stored on Day 18
        print(f"--- Result {i} | source: {doc.metadata['source']} | chunk {doc.metadata['chunk_id']} ---")
        print(doc.page_content)
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python retrieve.py <question>")
        sys.exit(1)

    # Join all args so a multi-word question without quotes still works
    question = " ".join(sys.argv[1:])

    results = retrieve(question)
    print_results(question, results)