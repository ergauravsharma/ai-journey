import os
import sys
from dotenv import load_dotenv
from load_index import load_index  # Day 18: opens the saved Chroma index, no re-embedding
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
     "rather than guessing.\n\nContext:\n{context}"),
    ("user", "{question}"),
])


def format_context(chunks: list) -> str:
    """Join retrieved chunks into one block of text, labeled by source, for the prompt."""
    parts = []
    for doc in chunks:
        parts.append(f"[Source: {doc.metadata['source']}]\n{doc.page_content}")
    return "\n\n".join(parts)


def answer(question: str, k: int = 5) -> str:
    """Retrieve relevant chunks for a question, then generate an answer grounded in them."""

    # Step 1: retrieve, same logic as Day 19
    vector_store = load_index()
    chunks = vector_store.similarity_search(question, k=k)

    # Step 2: build the prompt's context from those chunks
    context = format_context(chunks)

    # Step 3: generate, filling in the prompt template and sending it to the LLM
    chain = prompt | llm
    response = chain.invoke({"context": context, "question": question})

       # response.content can be a plain string or a list of parts (text + internal
       # reasoning data) depending on the model. Handle both cases.
    if isinstance(response.content, str):
        return response.content

    text_parts = [part["text"] for part in response.content if part.get("type") == "text"]
    return "\n".join(text_parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rag.py <question>")
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = answer(question)

    print(f'Question: "{question}"\n')
    print(f"Answer: {result}")