import sqlite3, time
import pytest
from sqlagent import db

@pytest.fixture
def sample(tmp_path, monkeypatch):
    p = tmp_path / 's.db'
    c = sqlite3.connect(p); c.execute('CREATE TABLE ponds (id INT, name TEXT)'); c.execute("INSERT INTO ponds VALUES (1,'a')"); c.commit(); c.close()
    monkeypatch.setenv('SQLAGENT_DB', str(p)); return p

def test_select_works(sample):
    cols, rows = db.run_readonly('SELECT * FROM ponds')
    assert cols == ['id', 'name'] and rows == [(1, 'a')]

def test_writes_fail_even_if_validation_were_bypassed(sample):
    with pytest.raises(sqlite3.OperationalError):
        db.run_readonly('DELETE FROM ponds')
    assert db.run_readonly('SELECT COUNT(*) FROM ponds')[1] == [(1,)]

def test_runaway_query_is_interrupted(sample):
    t = time.time()
    with pytest.raises(sqlite3.OperationalError):
        db.run_readonly('WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM r) SELECT COUNT(*) FROM r', timeout_s=0.5)
    assert time.time() - t < 5
