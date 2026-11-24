"""The gold SQL itself must be valid, allowed and runnable on the sample database."""
import sys, yaml
sys.path.insert(0, 'scripts')
from make_sample_db import build
from sqlagent.db import run_readonly
from sqlagent.validate import validate

def test_all_golden_queries_validate_and_return_rows(tmp_path, monkeypatch):
    build(str(tmp_path / 's.db')); monkeypatch.setenv('SQLAGENT_DB', str(tmp_path / 's.db'))
    for c in yaml.safe_load(open('eval/golden.yml')):
        cols, rows = run_readonly(validate(c['sql']))
        assert rows, c['q']
