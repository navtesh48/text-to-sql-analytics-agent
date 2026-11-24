"""Agent loop. Tools: run_sql (explore/test, errors come back so the model can fix its query) and
finish (deliver the answer). Layer 3 of 3 safety: a hard cap on steps."""
import json, pathlib
import pandas as pd
from anthropic import Anthropic
from sqlagent.llm import MODEL
from sqlagent.validate import validate, Rejected
from sqlagent.db import run_readonly
from sqlagent import feedback

SEMANTIC = pathlib.Path(__file__).resolve().parents[2].joinpath('semantic.yml').read_text()
TOOLS = [
  {'name': 'run_sql', 'description': 'Run ONE read-only SQLite SELECT. Returns column names, up to 30 rows, and the total row count, '
   'or an error message you should use to fix the query.',
   'input_schema': {'type': 'object', 'properties': {'sql': {'type': 'string'}}, 'required': ['sql']}},
  {'name': 'finish', 'description': 'Deliver the final answer once you have verified the SQL returns what the question asks.',
   'input_schema': {'type': 'object', 'properties': {
      'answer': {'type': 'string', 'description': '1-3 sentences in plain English with the key numbers.'},
      'sql': {'type': 'string', 'description': 'The exact final query that supports the answer.'},
      'chart': {'type': 'object', 'properties': {
          'type': {'type': 'string', 'enum': ['bar', 'line', 'scatter', 'none']},
          'x': {'type': 'string'}, 'y': {'type': 'string'}}, 'required': ['type']}},
    'required': ['answer', 'sql', 'chart']}},
]

def _system(question: str) -> str:
    ex = ''.join(f'\nQ: {q}\nSQL: {s}\n' for q, s in feedback.similar(question))
    return ('You are a careful data analyst answering questions about an algae farm database. Use ONLY the schema below. '
            'Always test your SQL with run_sql before calling finish. Never invent numbers; every number in your answer must '
            'come from a query result. If the question cannot be answered from the data, say so in finish with chart type none. '
            'Ambiguous terms: pick the most reasonable meaning and state it in the answer.\n\n'
            f'SCHEMA AND METRICS:\n{SEMANTIC}\n' + (f'\nVERIFIED EXAMPLES:{ex}' if ex else ''))

def _tool_run(sql: str) -> dict:
    try:
        safe = validate(sql)
        cols, rows = run_readonly(safe)
        return {'columns': cols, 'rows': [list(r) for r in rows[:30]], 'total_rows': len(rows), 'sql_run': safe}
    except Rejected as e:
        return {'error': f'rejected: {e}'}
    except Exception as e:
        return {'error': f'database error: {e}'}

def ask(question: str, max_steps: int = 6) -> dict:
    client = Anthropic()
    msgs = [{'role': 'user', 'content': question}]
    for _ in range(max_steps):
        resp = client.messages.create(model=MODEL, max_tokens=1500, system=_system(question), tools=TOOLS, messages=msgs)
        msgs.append({'role': 'assistant', 'content': resp.content})
        calls = [b for b in resp.content if b.type == 'tool_use']
        if not calls:
            return {'answer': ''.join(b.text for b in resp.content if b.type == 'text'), 'sql': None, 'df': None, 'chart': {'type': 'none'}}
        done = next((b for b in calls if b.name == 'finish'), None)
        if done:
            a = done.input
            df = None
            try:
                cols, rows = run_readonly(validate(a['sql']))
                df = pd.DataFrame(rows, columns=cols)
            except Exception:
                pass
            return {'answer': a['answer'], 'sql': a['sql'], 'df': df, 'chart': a.get('chart', {'type': 'none'})}
        results = [{'type': 'tool_result', 'tool_use_id': b.id, 'content': json.dumps(_tool_run(b.input['sql']), default=str)} for b in calls]
        msgs.append({'role': 'user', 'content': results})
    return {'answer': 'I could not complete this within the step limit.', 'sql': None, 'df': None, 'chart': {'type': 'none'}}
