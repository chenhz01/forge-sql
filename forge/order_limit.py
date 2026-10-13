# -*- coding: utf-8 -*-
"""forge.order-limit — ORDER BY salary DESC with LIMIT over employees.

Problem: report the top-k rows (id, salary) under ORDER BY salary DESC,
with id ASC as a deterministic tie-breaker. Graded by REBUILDING the
database from meta and executing the query — the oracle is SQLite itself.
The answer list is never trusted.
"""
import random

from .common import make_id, int_knob, build_db, DEPTS

TYPE = "order-limit"


def _gen_table(rng, n):
    rows = []
    for i in range(1, n + 1):
        rows.append((i, "emp%02d" % i, rng.choice(DEPTS), rng.randrange(30, 99) * 100))
    return rows


def _top_rows(conn, sql):
    cur = conn.execute(sql)
    return [[int(row[0]), int(row[1])] for row in cur.fetchall()]


def generate(seed, difficulty=0.5):
    rng = random.Random("order-limit|%d" % seed)
    n = int_knob(difficulty, 8, 20)
    rows = _gen_table(rng, n)
    k = int_knob(difficulty, 3, 6)
    query = ("SELECT id, salary FROM employees "
             "ORDER BY salary DESC, id ASC LIMIT %d" % k)
    conn = build_db({"tables": {"employees": rows}})
    top = _top_rows(conn, query)
    conn.close()
    return {
        "id": make_id(TYPE, seed),
        "type": TYPE,
        "difficulty": float(difficulty),
        "seed": int(seed),
        "prompt": ("Table employees(id, name, dept, salary) has %d rows, e.g. %s.\n"
                   "List the top %d rows by salary as a JSON array of [id, salary] "
                   "pairs, highest salary first; break ties by smaller id first.\n\n"
                   "```sql\n%s\n```" % (n, rows[:3], k, query)),
        "answer": {"top": top},
        "solution": ("Ordering by salary DESC with id ASC as tie-breaker and "
                     "keeping %d rows yields %s." % (k, top)),
        "meta": {"tables": {"employees": rows}, "query": query},
    }


def verify(problem):
    try:
        conn = build_db(problem["meta"])
        got = _top_rows(conn, problem["meta"]["query"])
        conn.close()
        return got == problem["answer"]["top"]
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
    p["answer"]["top"][0][1] = p["answer"]["top"][0][1] + 100
    cases.append(("verify-false-wrong-salary", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["query"] = p["meta"]["query"].replace("DESC", "ASC")
    cases.append(("verify-false-tampered-query", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    n_rows = len(p["meta"]["tables"]["employees"])
    p["meta"]["tables"]["employees"].append((n_rows + 1, "empXX", DEPTS[0], 9999999))
    cases.append(("verify-false-tampered-data", lambda p=p: verify(p) is False))
    from .common import schema_ok
    cases.append(("schema-ok", lambda: schema_ok(generate(42, 0.3))))
    def _tie_break_helper():
        conn = build_db({"tables": {"employees": [
            (1, "a", "eng", 5000), (2, "b", "hr", 5000), (3, "c", "sales", 9000)]}})
        got = _top_rows(conn, "SELECT id, salary FROM employees "
                              "ORDER BY salary DESC, id ASC LIMIT 2")
        conn.close()
        return got == [[3, 9000], [1, 5000]]
    cases.append(("tie-break-helper", _tie_break_helper))
    return cases
