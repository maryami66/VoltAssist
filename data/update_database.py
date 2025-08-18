import os
import json
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.models import PointStruct
from openai import OpenAI

load_dotenv()
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")
embedding_model = "text-embedding-3-small"
collection_name = "faq_collection"

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)

# to delete if needed
# qdrant_client.delete_collection(collection_name)

openai_client = OpenAI(api_key=openai_api_key)

qdrant_client.create_collection(
    collection_name="faq_collection",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

with open("faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)


# define the embedding models
questions = [i['question'] for i in faqs]
embeddings = []
for q in questions:
    embedding_response = openai_client.embeddings.create(
        model=embedding_model,
        input=q
    )
    embeddings.append(embedding_response.data[0].embedding)

# Load the appropriate encoder for the embedding model
print(qdrant_client.get_collections())

points = []
for item, vector in zip(faqs, embeddings):
    # 5a) Generate embedding
    point = PointStruct(
        id=item["id"],
        vector=vector,
        payload={
            "question": item["question"],
            "answer": item["answer"],
        }
    )
    points.append(point)

qdrant_client.upsert(
    collection_name=collection_name,
    points=points
)

# points = qdrant_client.scroll(
#     collection_name=collection_name,
#     limit=1
# )
# print(points)
