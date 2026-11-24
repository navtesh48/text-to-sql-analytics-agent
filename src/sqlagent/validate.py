"""Layer 1 of 3: parse with sqlglot; allow exactly one SELECT over whitelisted tables; add a LIMIT."""
import sqlglot
from sqlglot import exp

ALLOWED = {'strains', 'ponds', 'harvests', 'daily'}
BANNED = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command, exp.Pragma)

class Rejected(ValueError): pass

def validate(sql: str, max_rows: int = 500) -> str:
    try:
        stmts = [s for s in sqlglot.parse(sql, read='sqlite') if s is not None]
    except sqlglot.errors.ParseError as e:
        raise Rejected(f'SQL does not parse: {e}')
    if len(stmts) != 1: raise Rejected('exactly one statement allowed')
    tree = stmts[0]
    if not isinstance(tree, (exp.Select, exp.Union)): raise Rejected('only SELECT is allowed')
    if any(isinstance(n, BANNED) for n in tree.walk()): raise Rejected('write operations are not allowed')
    ctes = {c.alias for c in tree.find_all(exp.CTE)}
    tables = {t.name for t in tree.find_all(exp.Table)} - ctes
    unknown = tables - ALLOWED
    if unknown: raise Rejected(f'unknown tables: {sorted(unknown)}; allowed: {sorted(ALLOWED)}')
    if not tree.args.get('limit'): tree = tree.limit(max_rows)
    return tree.sql(dialect='sqlite')
