import os
import json
from dotenv import load_dotenv
import time
import streamlit as st
from rag import retriever
from openai import OpenAI

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=openai_api_key)


def build_prompt(user_query):
    """
    Combine a system instruction, the retrieved document snippets, and the user query
    into a single prompt for the ChatCompletion API.
    """
    system_instructions = (
        "You are VoltAssist, a helpful AI assistant for an online electronics store. "
        "Use the product manuals and FAQ snippets below to answer customer questions accurately. "
        "If the answer is not in the documents, answer truthfully that you don't have enough information."
    )

    # Prefix each snippet with a separator
    context = retriever(user_query)

    prompt = (
        f"{system_instructions}\n\n"
        f"---\n"
        f"{context}\n"
        f"---\n\n"
        f"Customer asks: \"{user_query}\"\n"
        f"AI:"
    )
    return prompt


def generate_response(prompt: str) -> str:
    """
    Calls Azure OpenAI's ChatCompletion endpoint via the chat‐style API,
    but passing our entire prompt as a single user message to a conversation.
    """
    completion = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": prompt}
        ],
        model="gpt-4o-mini",
        max_tokens=512,
        temperature=0.2,
        n=1,
        stop=None
    )
    return completion.choices[0].message.content.strip()


st.set_page_config(
    page_title="Volt Assist",
    page_icon="🤖",
    layout="centered"
)


with st.sidebar:
    st.title("Settings")
    available_languages = [
        "English", "Spanish", "French", "German", "Chinese", "Japanese", "Arabic"
    ]
    selected_languages = st.multiselect(
        "Select languages:", available_languages,
        default=["English"]
    )
    st.markdown(
        "**Selected:** " + ", ".join(selected_languages)
        if selected_languages else "None"
    )


def handle_popup_delay():
    if 'show_ai' not in st.session_state:
        st.session_state.show_ai = False
    if not st.session_state.show_ai:
        # Keep page blank for a short time before showing chat
        time.sleep(3)
        st.session_state.show_ai = True


handle_popup_delay()


def init_chat():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How can I help you?"}
        ]


init_chat()


def display_chat():
    for msg in st.session_state.messages:
        if msg['role'] == 'assistant':
            st.chat_message("assistant").markdown(msg['content'])
        else:
            st.chat_message("user").markdown(msg['content'])


display_chat()

# user_input = "I want to sign up, what info do I need?"
if user_input := st.chat_input("Type your message..."):
    prompt = build_prompt(user_input)
    print(prompt)
    response = generate_response(prompt)
    # Call OpenAI ChatCompletion
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.chat_message("assistant"):
        st.write(response)


# Footer
st.markdown("---")
st.markdown("Powered by OpenAI GPT API")
