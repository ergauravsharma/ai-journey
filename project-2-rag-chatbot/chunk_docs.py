from pathlib import Path  # Path makes it easy to work with folders and files
from langchain_text_splitters import RecursiveCharacterTextSplitter  # the splitter that cuts text into chunks
from pypdf import PdfReader  # reads text out of PDF files

# Folder that holds our documents, built relative to this script's location
# so it works no matter which folder you run the script from
DOCS_DIR = Path(__file__).parent / "docs"


def load_documents(docs_dir: Path) -> list[dict]:
    """Read every .txt and .pdf file in a folder and return their text with the filename."""
    documents = []  # will hold one dict per file: {"source": filename, "text": full text}

    # sorted() keeps the file order the same every run, which makes results predictable
    for file_path in sorted(docs_dir.iterdir()):
        if file_path.suffix == ".txt":
            # Plain text files can be read directly
            text = file_path.read_text(encoding="utf-8")
        elif file_path.suffix == ".pdf":
            # PDFs are split into pages, so we read each page and join them together
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            continue  # skip any file type we don't support

        documents.append({"source": file_path.name, "text": text})

    return documents


def chunk_documents(documents: list[dict], chunk_size: int = 300, chunk_overlap: int = 50) -> list[dict]:
    """Split each document into overlapping chunks, keeping track of which file each came from."""

    # The splitter tries to break at paragraphs first, then sentences, then words,
    # so chunks end at natural boundaries instead of in the middle of a word
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,        # maximum characters per chunk
        chunk_overlap=chunk_overlap,  # characters repeated between neighbouring chunks
    )

    chunks = []  # will hold one dict per chunk

    for doc in documents:
        pieces = splitter.split_text(doc["text"])  # returns a list of text pieces
        for i, piece in enumerate(pieces):
            # Store the source file and position with each chunk. RAG needs the
            # source later so the chatbot can cite where an answer came from (Day 22)
            chunks.append({
                "source": doc["source"],
                "chunk_id": i,
                "text": piece,
            })

    return chunks


if __name__ == "__main__":
    docs = load_documents(DOCS_DIR)
    print(f"Loaded {len(docs)} documents\n")

    # Temporary experiment: small chunks force long paragraphs to split, so we can see overlap
    chunks = chunk_documents(docs, chunk_size=150, chunk_overlap=30)
    print(f"Produced {len(chunks)} chunks in total\n")

    # Print every chunk so we can eyeball whether the splits look clean
    for chunk in chunks:
        print(f"[{chunk['source']} | chunk {chunk['chunk_id']} | {len(chunk['text'])} chars]")
        print(chunk["text"])
        print("-" * 60)