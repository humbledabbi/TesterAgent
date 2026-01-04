import math
import sqlite3
from typing import Optional
from Semantic_Migration import embed_text
import json

def cosine_similarity(a,b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)

SIMILARITY_THRESHOLD = 0.8
DB_PATH = "ai_test_memory.db"

def find_semantic_match(step_text:str, page_url:str) -> Optional[dict]:
    query_embedding = embed_text(step_text)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
            SELECT id, goal, code, embedding, page_url
            FROM test_memory
            WHERE embedding IS NOT NULL
        """)

    best_match = None
    best_score = 0.0

    for row_id, goal, code, embedding_json, stored_page in cursor.fetchall():
        stored_embedding = json.loads(embedding_json)
        score = cosine_similarity(query_embedding, stored_embedding)
        if stored_page == page_url:
            score += 0.05

        if score > best_score:
            best_score = score
            best_match = {
                "id": row_id,
                "goal": goal,
                "code": code,
                "score": score,
                "page_url": stored_page
            }
    conn.close()

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        print(f"Semantic match found (score={best_score:.3f}) → {best_match['goal']}")
        return best_match
    return None



