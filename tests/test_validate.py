import pytest
from sqlagent.validate import validate, Rejected

def test_adds_limit():
    assert 'LIMIT 500' in validate('SELECT * FROM ponds')

def test_keeps_existing_limit():
    assert 'LIMIT 5' in validate('SELECT * FROM ponds LIMIT 5') and 'LIMIT 500' not in validate('SELECT * FROM ponds LIMIT 5')

@pytest.mark.parametrize('bad', [
    'DROP TABLE ponds', 'DELETE FROM ponds', 'SELECT 1; SELECT 2',
    'SELECT * FROM sqlite_master', 'UPDATE ponds SET name=1', 'PRAGMA table_info(ponds)',
    "INSERT INTO ponds VALUES (99,'x',1,1,'x')", 'SELECT * FROM ponds; DROP TABLE ponds',
    'ATTACH DATABASE "x.db" AS x'])
def test_rejects(bad):
    with pytest.raises(Rejected): validate(bad)

def test_cte_ok():
    validate('WITH x AS (SELECT * FROM ponds) SELECT * FROM x')

def test_union_ok():
    validate('SELECT id FROM ponds UNION SELECT id FROM strains')
