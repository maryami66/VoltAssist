import json
from openai import OpenAI
from typing import List
from rag import retriever


class OpenAIClient:
    def __init__(self, openai_api_key, category, languages):
        self.client = OpenAI(api_key=openai_api_key)
        self.language = languages
        self.category = category

    def build_prompt(self, user_query):
        """
        Combine a system instruction, the retrieved document snippets, and the user query
        into a single prompt for the ChatCompletion API.
        """
        examples = retriever(user_query, self.category)

        system_prompt = f"""
        You are VoltAssist, a helpful AI assistant for an online electronics store. 
        Use the product manuals and FAQ snippets below to answer customer questions accurately. 
        If the answer is not in the documents, answer truthfully that you don't have enough information, and tell user to select the **relevant category** from the option first to get better response.
        ```
        {examples}
        ```
        answer in {self.language}
        """

        user_prompt = f"""
        Customer asks: {user_query}
        """

        messages = [
                       {"role": "system", "content": system_prompt},
                       {"role": "user", "content": user_prompt},
                   ]
        return messages

    def generate_response(self, messages: List) -> str:
        """
        Calls Azure OpenAI's ChatCompletion endpoint via the chat‐style API,
        but passing our entire prompt as a single user message to a conversation.
        """
        completion = self.client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=512,
            temperature=0.2,
            n=1,
            stop=None
        )
        return completion.choices[0].message.content.strip()
