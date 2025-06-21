import json

with open("../data/faqs.json", "r", encoding="utf-8") as f:
    faqs = json.load(f)

categories = list(set([f["category"] for f in faqs]))
print(categories)

