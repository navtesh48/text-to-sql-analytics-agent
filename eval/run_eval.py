"""Execution accuracy: a case passes when the agent's result set equals the gold result set
(order-insensitive, floats rounded to 2 places).   run: PYTHONPATH=src python eval/run_eval.py"""
import yaml
from sqlagent.agent import ask
from sqlagent.db import run_readonly

def norm(rows): return sorted(tuple(round(v, 2) if isinstance(v, float) else v for v in r) for r in rows)

cases = yaml.safe_load(open('eval/golden.yml'))
ok = 0
for c in cases:
    r = ask(c['q'])
    try:
        got = norm(run_readonly(r['sql'])[1]) if r['sql'] else None
        want = norm(run_readonly(c['sql'])[1])
        passed = got == want
    except Exception:
        passed = False
    ok += passed
    print('PASS' if passed else 'FAIL', c['q'])
print(f'execution accuracy {ok}/{len(cases)}')
