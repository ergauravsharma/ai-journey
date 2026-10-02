from rag import answer

history = []

questions = [
    "How much does the Basic plan cost?",
    "What about the Pro plan?",  # "What about" only makes sense with history
    "Which one has more storage?",  # "which one" refers to the two plans just discussed
]

for q in questions:
    result = answer(q, history=history)
    print(f'Q: "{q}"')
    print(f"A: {result['answer']}")
    print(f"Sources: {', '.join(result['sources'])}\n")

    # Add this turn to history so the next question can reference it
    history.append({"question": q, "answer": result["answer"]})