import streamlit as st
from langchain_triage import triage

st.set_page_config(page_title="Support Ticket Triage", page_icon="🎫")

st.title("🎫 Support Ticket Triage")
st.write("Paste a support ticket below and get an instant classification + draft reply.")

EXAMPLES = {
    "Billing issue": "I was charged twice for my subscription this month. My card shows two separate charges of $29.99 on the same day, October 3rd. Can you please refund the duplicate charge?",
    "Technical bug": "The app crashes every time I try to upload a photo larger than 5MB. I'm using the latest version on Android 14.",
    "Urgent outage": "URGENT: Our entire team of 50 users has been locked out of the platform since this morning. This is blocking our production deployment scheduled for today.",
}


st.write("** Try an example:**")
cols = st.columns(len(EXAMPLES))
for col, (label,text) in zip(cols,EXAMPLES.items()):
    if col.button(label):
        st.session_state["ticket_text"] = text

ticket_text = st.text_area(
    "Ticket text",
    height=150,
    placeholder="Paste the customer's message here...",
    key="ticket_text",
)


if st.button("Triage Ticket", type="primary"):
    if not ticket_text or not ticket_text.strip():
        st.warning("Please paste some ticket text first.")
    elif len(ticket_text) > 5000:
        st.warning("That's a long ticket — please keep it under 5000 characters for best results.")
    else:
        try:
            with st.spinner("Analyzing ticket..."):
                result = triage(ticket_text)

            st.subheader("Result")

            col1, col2, col3 = st.columns(3)
            col1.metric("Category", result.category.value)
            col2.metric("Priority", result.priority.value)
            col3.metric("Sentiment", result.sentiment.value)

            st.write(f"**Confidence:** {result.confidence:.0%}")
            if result.confidence < 0.7:
                st.info("⚠️ Lower confidence — this ticket may need human review.")

            st.subheader("Draft Reply")
            st.write(result.draft_reply)

        except Exception as e:
            st.error(f"Something went wrong while analyzing this ticket. Please try again in a moment.")
            st.caption(f"Technical details: {e}")