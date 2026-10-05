import streamlit as st
from rag import answer  # Day 21-23's retrieve-prompt-generate chain, with memory and citations

st.set_page_config(page_title="CloudDesk Support Chat", page_icon="💬")

st.title("💬 CloudDesk Support Chat")
st.write("Ask a question about CloudDesk's refund policy, pricing plans, or troubleshooting.")

# session_state persists across reruns within one browser session, which is what lets
# the chat remember earlier turns instead of resetting every time the page redraws.
# This is the same "history" list from Day 23's test_memory.py, just stored differently.
if "history" not in st.session_state:
    st.session_state.history = []  # list of {"question": ..., "answer": ...} dicts, same shape rag.py expects

# Redraw every past message on each rerun, since Streamlit reruns the whole script
# top to bottom on every interaction, it doesn't remember what was drawn before
for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["answer"])
        if turn.get("sources"):
            st.caption(f"Sources: {', '.join(turn['sources'])}")

# st.chat_input renders a fixed input box at the bottom of the page and returns
# the typed text only on the turn the user actually submits something
question = st.chat_input("Ask a question...")

if question:
    # Show the user's new message immediately, before waiting on the API call
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = answer(question, history=st.session_state.history)
            except Exception as e:
                st.error("Something went wrong while answering. Please try again in a moment.")
                st.caption(f"Technical details: {e}")
                result = None

        if result:
            st.write(result["answer"])
            if result["sources"]:
                st.caption(f"Sources: {', '.join(result['sources'])}")

            # Add this turn to history so the next question has it available,
            # same pattern as Day 23's test_memory.py loop
            st.session_state.history.append({
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
            })