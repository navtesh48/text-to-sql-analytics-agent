"""Read-only query execution: read-only connection, query_only pragma and a wall-clock timeout."""
import os, sqlite3, time

def db_path() -> str:
    return os.getenv('SQLAGENT_DB', 'data/sample.db')

def run_readonly(sql: str, max_rows: int = 500, timeout_s: float = 5.0):
    conn = sqlite3.connect(f'file:{db_path()}?mode=ro', uri=True)
    conn.execute('PRAGMA query_only=ON')
    start = time.time()
    conn.set_progress_handler(lambda: 1 if time.time() - start > timeout_s else 0, 10000)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
        return cols, rows
    finally:
        conn.close()
