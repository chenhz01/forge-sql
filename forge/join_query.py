# -*- coding: utf-8 -*-
"""forge.join-query — JOIN + GROUP BY + HAVING across employees and orders.

Problem: report the total order amount per employee (only employees that
have orders), filtered by a HAVING threshold. Graded by REBUILDING the
database from meta and executing the query — the oracle is SQLite itself.
The answer dict is never trusted.
"""
import random

from .common import make_id, int_knob, build_db, run_query, DEPTS

TYPE = "join-query"


def _gen_employees(rng, n):
    rows = []
    for i in range(1, n + 1):
        rows.append((i, "emp%02d" % i, rng.choice(DEPTS), rng.randrange(30, 99) * 100))
    return rows


def _gen_orders(rng, employees):
    """Some employees get orders, some don't; a few orders have emp_id
    pointing at non-existent employees."""
    orows = []
    oid = 1
    for (_eid, _name, _dept, _salary) in employees:
        if rng.random() < 0.7:
            for _ in range(rng.randrange(1, 4)):
                orows.append((oid, _eid, rng.randrange(200, 3000, 100)))
                oid += 1
    n = len(employees)
    for _ in range(2):
        orows.append((oid, n + 100 + rng.randrange(1, 10),
                      rng.randrange(200, 3000, 100)))
        oid += 1
    return orows


def _norm(value):
    v = float(value)
    return int(v) if v.is_integer() else round(v, 2)


def _totals(conn, sql):
    cur = conn.execute(sql)
    return {str(row[0]): _norm(row[1]) for row in cur.fetchall()}


def generate(seed, difficulty=0.5):
    rng = random.Random("join-query|%d" % seed)
    n = int_knob(difficulty, 8, 20)
    employees = _gen_employees(rng, n)
    orders = _gen_orders(rng, employees)
    conn = build_db({"tables": {"employees": employees, "orders": orders}})
    max_total = conn.execute(
        "SELECT COALESCE(MAX(t), 0) FROM (SELECT SUM(o.amount) AS t "
        "FROM employees e JOIN orders o ON o.emp_id = e.id "
        "GROUP BY e.name)").fetchone()[0]
    threshold = min(int_knob(difficulty, 500, 15000), max_total - 1)
    threshold = max(threshold, 0)
    query = ("SELECT e.name, SUM(o.amount) AS total FROM employees e "
             "JOIN orders o ON o.emp_id = e.id GROUP BY e.name "
             "HAVING SUM(o.amount) > %d" % threshold)
    agg = _totals(conn, query)
    conn.close()
    return {
        "id": make_id(TYPE, seed),
        "type": TYPE,
        "difficulty": float(difficulty),
        "seed": int(seed),
        "prompt": ("Tables: employees(id, name, dept, salary) with %d rows, e.g. %s; "
                   "orders(id, emp_id, amount) with %d rows, e.g. %s. Some orders "
                   "reference employees not in the table and some employees have no "
                   "orders.\n"
                   "Report the total order amount for each employee that has orders, "
                   "as a JSON object mapping employee name to total (only employees "
                   "whose total exceeds %d).\n\n```sql\n%s\n```"
                   % (n, employees[:3], len(orders), orders[:3], threshold, query)),
        "answer": {"agg": agg},
        "solution": ("Joining orders to employees on emp_id, grouping by name and "
                     "summing amounts with HAVING SUM(o.amount) > %d yields %s."
                     % (threshold, agg)),
        "meta": {"tables": {"employees": employees, "orders": orders},
                 "query": query},
    }


def verify(problem):
    try:
        conn = build_db(problem["meta"])
        got = _totals(conn, problem["meta"]["query"])
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
    cases.append(("verify-false-wrong-total", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["query"] += " HAVING SUM(o.amount) > 999999999"
    cases.append(("verify-false-tampered-query", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["tables"]["orders"].append(
        (10 ** 6, 1, 999999))
    cases.append(("verify-false-tampered-data", lambda p=p: verify(p) is False))
    from .common import schema_ok
    cases.append(("schema-ok", lambda: schema_ok(generate(42, 0.3))))
    def _norm_helper():
        return (_norm(7) == 7 and _norm(7.0) == 7
                and _norm(1234.5678) == 1234.57)
    cases.append(("norm-helper", _norm_helper))
    return cases
