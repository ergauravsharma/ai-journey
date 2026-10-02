import os
import sys
from dotenv import load_dotenv
from load_index import load_index  # Day 18: opens the saved Chroma index, no re-embedding
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# The LLM that will read the retrieved chunks and write the final answer
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    temperature=0.1,  # low temperature: we want answers grounded in the chunks, not creative ones
    max_output_tokens=1024,
    google_api_key=os.environ["GOOGLE_API_KEY"],
)

# The prompt template: {context} will hold the retrieved chunks, {question} the user's question.
# Telling the model to only use the context is what keeps it from making things up.
prompt = ChatPromptTemplate.from_messages([
    ("system",
    "You are a support assistant for CloudDesk. Answer the user's question using ONLY the "
    "context below. If the answer isn't in the context, say you don't have that information "
    "rather than guessing.\n\nEach piece of context is labeled with its source filename. "
    "After answering, list ONLY the source filenames you actually drew on to write the "
    "answer, not every source that was provided to you.\n\nContext:\n{context}"),
    ("user", "{question}"),
])

class GroundedAnswer(BaseModel):
    answer: str
    sources_used: list[str]  # filenames the LLM actually drew on to write the answer


def format_context(chunks: list) -> str:
    """Join retrieved chunks into one block of text, labeled by source, for the prompt."""
    parts = []
    for doc in chunks:
        parts.append(f"[Source: {doc.metadata['source']}]\n{doc.page_content}")
    return "\n\n".join(parts)


def answer(question: str, k: int = 5) -> dict:
    """Retrieve relevant chunks for a question, generate an answer, and return it with the sources actually used."""

    # Step 1: retrieve, same logic as Day 19
    vector_store = load_index()
    chunks = vector_store.similarity_search(question, k=k)

    # Step 2: build the prompt's context from those chunks
    context = format_context(chunks)

    # Step 3: generate, asking the model itself which sources it actually used,
    # rather than inferring it from retrieval distance (Day 22's lesson: distance
    # doesn't reliably predict usage)
    structured_llm = llm.with_structured_output(GroundedAnswer)
    chain = prompt | structured_llm
    result: GroundedAnswer = chain.invoke({"context": context, "question": question})

    return {"answer": result.answer, "sources": result.sources_used}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rag.py <question>")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = answer(question)

    print(f'Question: "{question}"\n')
    print(f"Answer: {result['answer']}\n")
    print(f"Sources: {', '.join(result['sources'])}")