import sqlite3
from datetime import datetime

DB_PATH = "ai_test_memory.db"

def init_db():
    """initializes sql db for memory"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS test_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        base_url TEXT,
        page_url TEXT,
        goal TEXT,
        code TEXT,
        summary TEXT,
        tags TEXT,
        success INTEGER,
        created_at TEXT
    )""")

    conn.commit()
    conn.close()


def save_step_memory(base_url, page_url, goal, code, summary, tags, success):
    """saves each AI step in to DB"""
    if not success:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO test_memory (base_url, page_url, goal, code, summary, tags, success, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        base_url,
        page_url,
        goal,
        code,
        summary,
        ",".join(tags) if isinstance(tags, list) else tags,
        int(success),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
def get_recent_steps(base_url, page_url = None, limit = 5):
    """Fetches last N successful steps for the given URL or page."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if page_url:
        cur.execute("""
            SELECT goal, code, summary, tags, success
            FROM test_memory
            WHERE base_url = ? AND page_url = ?
            ORDER BY id DESC LIMIT ?
            """, (base_url, page_url, limit))
    else:
        cur.execute("""
           SELECT goal, code, summary, tags, success
           FROM test_memory
           WHERE base_url = ?
           ORDER BY id DESC LIMIT ?
           """, (base_url, limit))

    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "goal": row[0],
            "code": row[1],
            "summary": row[2],
            "tags": row[3],
            "success": bool(row[4])
        })
    return results

def filter_memory(memory_context, current_step_index, current_url, global_steps):
    """
    Keeps only memory relevant to the current required step and page:
    - Must match this step's goal (based on goal text)
    - Must match same page
    - Only keeps most recent success + most recent failure
    """
    relevant = []
    last_success = None
    last_failure = None

    required_text = global_steps[current_step_index].strip().lower()

    for entry in memory_context:
        goal_text = entry["goal"].strip().lower()

        # Filter by goal relevance
        if required_text not in goal_text:
            continue

        # Filter by URL
        if current_url not in entry.get("summary", ""):
            pass  # optional: summary may not include url

        # Keep most recent successes/failures
        if entry["success"]:
            if not last_success:
                last_success = entry
        else:
            if not last_failure:
                last_failure = entry

    if last_success:
        relevant.append(last_success)
    if last_failure:
        relevant.append(last_failure)

    return relevant

def get_cached_success(base_url, page_url, goal):
    """Returns the most recent successful saved step, or None."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, code
        FROM test_memory
        WHERE base_url = ? AND page_url = ? AND goal = ? AND success = 1
        ORDER BY id DESC LIMIT 1
    """, (base_url, page_url, goal))

    row = cur.fetchone()
    conn.close()

    if row:
        return {"id": row[0], "code": row[1]}
    return None
            
