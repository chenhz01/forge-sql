# -*- coding: utf-8 -*-
"""forge.aggregate-query — GROUP BY aggregation over the seeded employees table.

Problem: report the per-department aggregate (COUNT / SUM / AVG of salary).
Graded by REBUILDING the database from meta and executing the query — the
oracle is SQLite itself. The answer dict is never trusted.
"""
import random

from .common import make_id, int_knob, build_db, DEPTS

TYPE = "aggregate-query"


def _gen_table(rng, n):
    rows = []
    for i in range(1, n + 1):
        rows.append((i, "emp%02d" % i, rng.choice(DEPTS), rng.randrange(30, 99) * 100))
    return rows


def _round_value(agg_fn, value):
    if agg_fn == "AVG":
        return round(value, 2)
    return value


def _aggregate(conn, sql, agg_fn):
    cur = conn.execute(sql)
    return {str(row[0]): _round_value(agg_fn, row[1]) for row in cur.fetchall()}


def generate(seed, difficulty=0.5):
    rng = random.Random("aggregate-query|%d" % seed)
    n = int_knob(difficulty, 8, 20)
    rows = _gen_table(rng, n)
    agg_fn = rng.choice(["COUNT", "SUM", "AVG"])
    fn_sql = {"COUNT": "COUNT(*)", "SUM": "SUM(salary)", "AVG": "AVG(salary)"}[agg_fn]
    query = ("SELECT dept, %s FROM employees GROUP BY dept ORDER BY dept"
             % fn_sql)
    conn = build_db({"tables": {"employees": rows}})
    agg = _aggregate(conn, query, agg_fn)
    conn.close()
    return {
        "id": make_id(TYPE, seed),
        "type": TYPE,
        "difficulty": float(difficulty),
        "seed": int(seed),
        "prompt": ("Table employees(id, name, dept, salary) has %d rows, e.g. %s. "
                   "Departments: %s.\n"
                   "For each department, report the %s of salary as a JSON object "
                   "mapping dept to value%s.\n\n```sql\nSELECT dept, %s FROM employees "
                   "GROUP BY dept;\n```"
                   % (n, rows[:3], ", ".join(DEPTS), agg_fn,
                      " rounded to 2 decimals" if agg_fn == "AVG" else "", fn_sql)),
        "answer": {"agg": agg},
        "solution": ("Grouping by dept and applying %s(salary) yields %s."
                     % (agg_fn, agg)),
        "meta": {"tables": {"employees": rows}, "query": query, "agg_fn": agg_fn},
    }


def verify(problem):
    try:
        meta = problem["meta"]
        conn = build_db(meta)
        got = _aggregate(conn, meta["query"], meta["agg_fn"])
        conn.close()
        return got == problem["answer"]["agg"]
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
    some_key = next(iter(p["answer"]["agg"]))
    p["answer"]["agg"][some_key] = p["answer"]["agg"][some_key] + 1
    cases.append(("verify-false-wrong-value", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["query"] += " HAVING COUNT(*) > 0"
    cases.append(("verify-false-tampered-query", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    n_rows = len(p["meta"]["tables"]["employees"])
    p["meta"]["tables"]["employees"].append((n_rows + 1, "empXX", DEPTS[0], 100))
    cases.append(("verify-false-tampered-data", lambda p=p: verify(p) is False))
    from .common import schema_ok
    cases.append(("schema-ok", lambda: schema_ok(generate(42, 0.3))))
    def _round_helper():
        return _round_value("AVG", 1234.5678) == 1234.57 and _round_value("SUM", 7) == 7
    cases.append(("round-helper", _round_helper))
    return cases
