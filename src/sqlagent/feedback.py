"""Thumbs-up answers become few-shot examples; the 3 most similar (word overlap) go into the prompt."""
import os, pathlib, sqlite3, re

_c: sqlite3.Connection

def connect(path: str | None = None) -> None:
    global _c
    path = path or os.getenv('SQLAGENT_FEEDBACK_DB', 'data/feedback.db')
    if path != ':memory:': pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    _c = sqlite3.connect(path, check_same_thread=False)
    _c.execute('CREATE TABLE IF NOT EXISTS good (question TEXT PRIMARY KEY, sql TEXT)')
    _c.execute('CREATE TABLE IF NOT EXISTS bad (question TEXT, sql TEXT, note TEXT)')

connect()

def _w(s): return set(re.findall(r'[a-z0-9]+', s.lower()))

def save_good(q, sql): _c.execute('INSERT OR REPLACE INTO good VALUES (?,?)', (q, sql)); _c.commit()
def save_bad(q, sql, note=''): _c.execute('INSERT INTO bad VALUES (?,?,?)', (q, sql, note)); _c.commit()

def similar(q: str, k: int = 3) -> list[tuple[str, str]]:
    qw = _w(q)
    scored = [(len(qw & _w(a)) / max(1, len(qw | _w(a))), a, s) for a, s in _c.execute('SELECT * FROM good')]
    return [(a, s) for sc, a, s in sorted(scored, reverse=True)[:k] if sc > 0.2]
