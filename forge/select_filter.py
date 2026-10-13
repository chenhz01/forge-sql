# -*- coding: utf-8 -*-
"""forge.select-filter — reference implementation.

Problem: given the seeded employees table and a SELECT query with WHERE,
report how many rows it returns. Graded by REBUILDING the database from
meta and executing the query — the oracle is SQLite itself.
"""
import random

from .common import make_id, int_knob, build_db, run_query, DEPTS

TYPE = "select-filter"


def _gen_table(rng, n):
    rows = []
    for i in range(1, n + 1):
        rows.append((i, "emp%02d" % i, rng.choice(DEPTS), rng.randrange(30, 99) * 100))
    return rows


def generate(seed, difficulty=0.5):
    rng = random.Random("select-filter|%d" % seed)
    n = int_knob(difficulty, 8, 20)
    rows = _gen_table(rng, n)
    dept = rng.choice(DEPTS)
    salary_min = rng.randrange(3000, 8000, 500)
    conds = ["dept = '%s'" % dept]
    if difficulty > 0.4:
        conds.append("salary >= %d" % salary_min)
    query = "SELECT * FROM employees WHERE %s" % " AND ".join(conds)
    conn = build_db({"tables": {"employees": rows}})
    expected = run_query(conn, query)
    conn.close()
    return {
        "id": make_id(TYPE, seed),
        "type": TYPE,
        "difficulty": float(difficulty),
        "seed": int(seed),
        "prompt": ("Table employees(id, name, dept, salary) has %d rows: %s.\n"
                   "How many rows does this query return?\n\n```sql\n%s\n```"
                   % (n, rows[:3], query)),
        "answer": {"row_count": len(expected)},
        "solution": "Running the query on the seeded table returns %d rows." % len(expected),
        "meta": {"tables": {"employees": rows}, "query": query},
    }


def verify(problem):
    try:
        conn = build_db(problem["meta"])
        got = run_query(conn, problem["meta"]["query"])
        conn.close()
        return len(got) == problem["answer"]["row_count"]
    except Exception:
        return False


def self_cases():
    import copy
    cases = []
    for sd in range(5):
        cases.append(("gen-deterministic-%d" % sd,
                      lambda sd=sd: generate(sd, 0.5) == generate(sd, 0.5)))
    for d in (0.0, 0.25, 0.5, 0.75, 1.0):
        cases.append(("verify-true-d%.2f" % d,
                      lambda d=d: verify(generate(123 + int(d * 100), d))))
    base = generate(7, 0.5)
    p = copy.deepcopy(base)
    p["answer"]["row_count"] += 1
    cases.append(("verify-false-wrong-count", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["query"] += " AND salary > 999999"
    cases.append(("verify-false-tampered-query", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["tables"]["employees"].pop()
    cases.append(("verify-false-tampered-data", lambda p=p: verify(p) is False))
    from .common import schema_ok
    cases.append(("schema-ok", lambda: schema_ok(generate(42, 0.3))))
    def _db_rows():
        from .common import build_db as _b
        conn = _b({"tables": {"employees": _gen_table(random.Random(1), 10)}})
        n = len(conn.execute("SELECT * FROM employees").fetchall())
        conn.close()
        return n == 10
    cases.append(("db-rebuild", _db_rows))
    return cases
