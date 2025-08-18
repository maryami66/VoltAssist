import pandas as pd
import json

df = pd.read_excel("faqs.xlsx")

print(df.columns)
records = df.to_dict(orient='records')

print(records)
with open('faqs.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
