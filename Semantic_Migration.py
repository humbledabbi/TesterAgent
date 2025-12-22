import sqlite3
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_KEY = os.getenv("OPEN_ROUTER_KEY")
JINA_APIKEY = os.getenv("JINA_API_KEY")

print("JINA_APIKEY =", JINA_APIKEY)
print("openrouter key =", OPENROUTER_KEY)
def embed_text(text: str) -> list[float]:
    response = requests.post(
        "https://api.jina.ai/v1/embeddings",
        headers={
            "Authorization": f"Bearer {JINA_APIKEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "jina-embeddings-v2-base-en",
            "input": [text]
        },
        timeout=30
    )

    response.raise_for_status()
    return response.json()["data"][0]["embedding"]

DB_PATH = "ai_test_memory.db"

def migrate_embeddings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    select id, goal, page_url
    from test_memory
    where embedding is NULL
    """)

    rows = cursor.fetchall()
    print(f" found {len(rows)} to embed")

    for row_id, goal, page_url in rows:
        semantic_text = f"{goal} | page = {page_url}"

        try:
            embedding = embed_text(semantic_text)
            cursor.execute(
                "update test_memory set embedding = ? where id = ?",
            (json.dumps(embedding), row_id)
            )

            conn.commit()
            time.sleep(0.3)
        except Exception as e:
            print(f"failed to embed id = {row_id} : {e}")
    conn.close()

if __name__ == "__main__":
    migrate_embeddings()