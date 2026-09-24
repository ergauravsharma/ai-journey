import streamlit as st
from langchain_triage import triage

st.set_page_config(page_title="Support Ticket Triage", page_icon="🎫")

st.title("🎫 Support Ticket Triage")
st.write("Paste a support ticket below and get an instant classification + draft reply.")

ticket_text = st.text_area("Ticket text", height=150, placeholder="Paste the customer's message here...")

if st.button("Triage Ticket"):
    if not ticket_text.strip():
        st.warning("Please paste some ticket text first.")
    else:
        with st.spinner("Analyzing ticket..."):
            result = triage(ticket_text)

        st.subheader("Result")

        col1, col2, col3 = st.columns(3)
        col1.metric("Category", result.category.value)
        col2.metric("Priority", result.priority.value)
        col3.metric("Sentiment", result.sentiment.value)

        st.write(f"**Confidence:** {result.confidence:.0%}")

        st.subheader("Draft Reply")
        st.write(result.draft_reply)