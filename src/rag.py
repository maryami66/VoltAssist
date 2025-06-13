import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

load_dotenv()
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
collection_name = "faq_collection"

openai_client = OpenAI(api_key=openai_api_key)

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)


def retriever(user_input):
    embedding_user_input = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=user_input
    ).data[0].embedding
    search_result = qdrant_client.query_points(
        collection_name=collection_name,
        query=embedding_user_input,
        with_payload=True,
        limit=2
    ).points
    search_result_sorted = sorted(search_result, key=lambda x: x.score, reverse=True)
    points = [{'Question': p.payload['question'], "Answer": p.payload['answer']} for p in search_result_sorted]

    return json.dumps(points)

