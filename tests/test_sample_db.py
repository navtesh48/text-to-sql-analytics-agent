import sys, sqlite3
sys.path.insert(0, 'scripts')
from make_sample_db import build

def test_sample_db_is_deterministic_and_populated(tmp_path):
    a = build(str(tmp_path / 'a.db')); b = build(str(tmp_path / 'b.db'))
    assert a == b and a[0] == 12 * 365 and a[1] > 0
    c = sqlite3.connect(tmp_path / 'a.db')
    assert c.execute('SELECT COUNT(*) FROM ponds').fetchone()[0] == 12
