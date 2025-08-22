import streamlit as st
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from llm import OpenAIClient
from streamlit_feedback import streamlit_feedback

parent_dir = Path(__file__).resolve().parent.parent
# create a .env file in VoltAssist directory
load_dotenv(parent_dir / ".env")
with open("data/faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

st.set_page_config(
    page_title="Volt Assist - A Q&A Bot",
    page_icon="🤖",
    layout="centered"
)
st.title("💬 VoltAssist – A Q&A Bot")
st.markdown("Ask any question about Shipping & Delivery, Warranty & Repairs, Customer Service & Contact, Product Information & Support, Ordering & Payment, Billing & Tax, Promotions & Gift Cards, Inventory & Availability, Account & Profile, Returns & Exchanges, and more. 🚀")

categories = list(set([f["category"] for f in faqs]))
category = st.radio("Please select the category for your question:", categories, horizontal=True, key="department")
available_languages = ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Arabic"]
st.session_state.selected_languages = st.selectbox(
    "Select languages:", available_languages,
)
if st.session_state.selected_languages is None:
    st.session_state.selected_languages = "English"

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAIClient(openai_api_key, category, st.session_state.selected_languages)

with st.sidebar:
    now = datetime.now()

    st.header("🗓️ Today")
    st.write(f"**Date:** {now:%A, %d %B %Y}")
    st.write(f"**Time:** {now:%H:%M:%S}")

    # support button
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("If **VoltAssist** cannot help, we are always here to support you with your question. Please **contact us**:", unsafe_allow_html=True)

    recipient_email = "support@example.com"
    subject = "Support Request"
    body = "Please describe the your question:"
    mailto_link = f"mailto:{recipient_email}?subject={subject}&body={body}"
    st.link_button(label="✉ Contact Support", url=mailto_link)
    st.markdown("---")
    st.caption("Built for customer support demos with Streamlit · Powered by OpenAI ✨")


# --- Question Input ---
quick_examples = [
    "How can I reset my password?",
    "What’s your refund policy?",
    "How can I place an order?",
]

user_question = st.chat_input("Write your question here!")

with st.container():
    st.markdown("**Quick questions:**")
    cols = st.columns(len(quick_examples))
    for idx, q in enumerate(quick_examples):
        if cols[idx].button(q, key=f"quick_{idx}"):
            user_question = q

if user_question:
    st.chat_message("human").write(user_question)
    st.session_state.messages = openai_client.build_prompt(user_question)
    print(st.session_state.messages)
    with st.spinner("Thinking…"):
        answer = openai_client.generate_response(st.session_state.messages)
    st.session_state.messages.append({"role": "Assistant", "content": answer})
    st.chat_message("ai").write(answer)

    streamlit_feedback(
            feedback_type="thumbs",
            align="flex-end",
            key="feedback_given",
            optional_text_label="Please give feedback to the answer",
        )
