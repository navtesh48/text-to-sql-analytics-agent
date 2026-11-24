# Text-to-SQL Analytics Agent

A chat interface over a database. Ask "which pond had the lowest yield in October?" and an agent writes SQL, validates it, runs it on a read-only connection, fixes its own errors, and returns a plain-English answer, the SQL, a table and a chart. The bundled database is a generated algae-farm dataset so it runs out of the box; point it at your own schema by editing `semantic.yml`.

> **Provenance:** a clean reimplementation of a project I originally built; the original code was unavailable, so this was rebuilt from the original design. The 22 tests pass, including the agent loop driven by a scripted fake model. I have **not** yet run it against the live Claude API, so no execution-accuracy number is reported. `eval/run_eval.py` is included to measure it.

## Three independent safety layers
1. **Validator** (`validate.py`): `sqlglot` parses the query. Exactly one `SELECT`/`UNION` over whitelisted tables, no write/DDL/PRAGMA nodes, and a `LIMIT` is added when missing.
2. **Database** (`db.py`): the SQLite connection is opened read-only with `PRAGMA query_only=ON` and a wall-clock timeout that interrupts runaway queries. Tests confirm writes fail even if validation were bypassed.
3. **Agent**: a hard cap of 6 steps per question.

## How it works
- **Semantic layer** (`semantic.yml`): table and column meanings, join paths, metric definitions (for example yield in g/L) and dialect notes. This is what makes a generic model useful on your data; extend it whenever the agent gets something wrong.
- **Agent loop** (`agent.py`): two tools, `run_sql` (explore and test; validation and database errors are returned so the model can fix its own query) and `finish` (answer, final SQL and chart spec). Every number in the answer must come from a query result.
- **Feedback memory** (`feedback.py`): "Good" answers are saved as question-to-SQL examples; the three most similar go into later prompts.
- **UI** (`app.py`): Streamlit chat with an SQL expander, results table, automatic Plotly chart and Good/Bad buttons.

## Quick start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # add ANTHROPIC_API_KEY
python scripts/make_sample_db.py           # generates data/sample.db
streamlit run src/sqlagent/app.py
```

## Evaluate
Add cases to `eval/golden.yml` (question + gold SQL; aim for about 20), then:
```bash
PYTHONPATH=src python eval/run_eval.py
```
Record the execution accuracy, add semantic-layer lines for what fails, and re-run to see the change.

## Tests
```bash
pytest     # validator rejections, read-only layer, timeout, agent loop with a fake model, golden SQL
```

## Roadmap
- Point at Postgres (change the sqlglot dialect and use a read-only role)
- Cache identical queries; add a query-plan tool
- Log questions, SQL and latency to a table and chart failures
