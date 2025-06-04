import os
import streamlit as st
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import openai

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION: replace the placeholders (or set these as environment vars)
# ─────────────────────────────────────────────────────────────────────────────

# Azure Cognitive Search settings
AZ_SEARCH_ENDPOINT = os.getenv("AZ_SEARCH_ENDPOINT", "<YOUR_SEARCH_ENDPOINT>")  # e.g., "https://<your-search-service>.search.windows.net"
AZ_SEARCH_KEY      = os.getenv("AZ_SEARCH_KEY", "<YOUR_SEARCH_ADMIN_KEY>")
AZ_SEARCH_INDEX    = os.getenv("AZ_SEARCH_INDEX", "<YOUR_INDEX_NAME>")         # e.g., "electronics-manuals"

# Azure OpenAI settings
AZ_OPENAI_API_BASE    = os.getenv("AZ_OPENAI_API_BASE", "<YOUR_AZURE_OPENAI_ENDPOINT>")  # e.g., "https://<your-openai-resource>.openai.azure.com/"
AZ_OPENAI_API_KEY     = os.getenv("AZ_OPENAI_API_KEY", "<YOUR_OPENAI_KEY>")
AZ_OPENAI_DEPLOYMENT  = os.getenv("AZ_OPENAI_DEPLOYMENT", "<YOUR_DEPLOYMENT_NAME>")      # e.g., "gpt-4o-deployment"
AZ_OPENAI_API_VERSION = "2023-05-15"  # or whatever version your resource uses

# ─────────────────────────────────────────────────────────────────────────────
# Initialize clients
# ─────────────────────────────────────────────────────────────────────────────

# Cognitive Search client
search_client = SearchClient(
    endpoint=AZ_SEARCH_ENDPOINT,
    index_name=AZ_SEARCH_INDEX,
    credential=AzureKeyCredential(AZ_SEARCH_KEY)
)

# OpenAI (Azure) configuration
openai.api_type        = "azure"
openai.api_key         = AZ_OPENAI_API_KEY
openai.api_base        = AZ_OPENAI_API_BASE
openai.api_version     = AZ_OPENAI_API_VERSION

# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page setup
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="GadgetGuru Customer Support", layout="wide")
st.title("🤖 GadgetGuru · AI Customer Support")

if "history" not in st.session_state:
    # Each message is a dict: {"role": "user" or "assistant", "content": str}
    st.session_state.history = []

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Retrieve top‐k relevant docs from Azure Cognitive Search
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_docs(query: str, top_k: int = 3):
    """
    Perform a semantic (or simple) search on Azure Cognitive Search.
    Returns a list of the top_k document contents (strings).
    """
    # You can adjust 'search_mode' and 'query_type' if using Semantic Search.
    results = search_client.search(
        search_text=query,
        top=top_k,
        include_total_count=False
    )
    snippets = []
    for doc in results:
        # Assume your index has a field called 'content' or 'text' containing the manual/faq text.
        # Adjust field name if needed.
        content = doc.get("content") or doc.get("text") or ""
        if content:
            snippets.append(content)
    return snippets

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Build a single prompt including retrieved contexts + user query
# ─────────────────────────────────────────────────────────────────────────────

def build_prompt(user_query: str, retrieved_texts: list[str]) -> str:
    """
    Combine a system instruction, the retrieved document snippets, and the user query
    into a single prompt for the ChatCompletion API.
    """
    system_instructions = (
        "You are GadgetGuru, a helpful AI assistant for an online electronics store. "
        "Use the product manuals and FAQ snippets below to answer customer questions accurately. "
        "If the answer is not in the documents, answer truthfully that you don't have enough information."
    )

    # Prefix each snippet with a separator
    context = "\n\n".join(f"Excerpt {i+1}:\n{txt}" for i, txt in enumerate(retrieved_texts))

    prompt = (
        f"{system_instructions}\n\n"
        f"---\n"
        f"{context}\n"
        f"---\n\n"
        f"Customer asks: \"{user_query}\"\n"
        f"AI:"
    )
    return prompt

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Invoke Azure OpenAI with a single‐turn prompt
# ─────────────────────────────────────────────────────────────────────────────

def generate_response(prompt: str) -> str:
    """
    Calls Azure OpenAI's ChatCompletion endpoint via the chat‐style API,
    but passing our entire prompt as a single user message to a conversation.
    """
    completion = openai.ChatCompletion.create(
        engine=AZ_OPENAI_DEPLOYMENT,            # your deployment name
        messages=[
            {"role": "system", "content": prompt}
        ],
        max_tokens=512,
        temperature=0.2,                       # lower temp for factual answers
        n=1,
        stop=None
    )
    return completion.choices[0].message.content.strip()

# ─────────────────────────────────────────────────────────────────────────────
# Main chat loop: display history & accept new user input
# ─────────────────────────────────────────────────────────────────────────────

# Display conversation so far
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.chat_message("User").markdown(msg["content"])
    else:
        st.chat_message("GadgetGuru").markdown(msg["content"])

# Accept new user input
user_input = st.chat_input("Type your question here…")

if user_input:
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.chat_message("User").markdown(user_input)

    # Step 1: Retrieve top‐k docs from Azure Cognitive Search
    retrieved = retrieve_docs(user_input, top_k=3)

    # Step 2: Build a prompt that combines retrieved docs + user question
    prompt = build_prompt(user_input, retrieved)

    # Step 3: Call Azure OpenAI to generate a response
    try:
        ai_reply = generate_response(prompt)
    except Exception as e:
        ai_reply = (
            "⚠️ Error generating response. "
            "Please check your Azure OpenAI configuration.\n\n"
            f"Details: {e}"
        )

    # Add AI reply to history & display
    st.session_state.history.append({"role": "assistant", "content": ai_reply})
    st.chat_message("GadgetGuru").markdown(ai_reply)
