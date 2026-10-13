# -*- coding: utf-8 -*-
"""forge.query-debug — pick the query whose result matches the expectation.

Problem: given the seeded employees table and four candidate queries
(A-D), identify the one that returns exactly `expected_rows` rows.
Exactly one candidate matches; distractors use a wrong dept, a flipped
comparison operator, or a missing condition. Graded by REBUILDING the
database from meta and executing all four candidates — the oracle is
SQLite itself. The answer is never trusted.
"""
import random

from .common import make_id, int_knob, build_db, run_query, DEPTS

TYPE = "query-debug"


def _gen_table(rng, n):
    rows = []
    for i in range(1, n + 1):
        rows.append((i, "emp%02d" % i, rng.choice(DEPTS), rng.randrange(30, 99) * 100))
    return rows


def _counts(rows, dept, other, smin):
    """Row counts for the reference query and its three distractors."""
    c_ref = len([r for r in rows if r[2] == dept and r[3] >= smin])
    c_wrong = len([r for r in rows if r[2] == other and r[3] >= smin])
    c_flip = len([r for r in rows if r[2] == dept and r[3] < smin])
    c_miss = len([r for r in rows if r[2] == dept])
    return c_ref, c_wrong, c_flip, c_miss


def generate(seed, difficulty=0.5):
    rng = random.Random("query-debug|%d" % seed)
    n = int_knob(difficulty, 8, 20)
    rows = None
    for _attempt in range(50):
        rows = _gen_table(rng, n)
        dept = rng.choice(DEPTS)
        other = rng.choice([d for d in DEPTS if d != dept])
        smin = rng.randrange(3000, 8000, 500)
        c_ref, c_wrong, c_flip, c_miss = _counts(rows, dept, other, smin)
        if len({c_ref, c_wrong, c_flip, c_miss}) == 4:
            break
    ref_q = ("SELECT * FROM employees WHERE dept = '%s' AND salary >= %d"
             % (dept, smin))
    options = {
        ref_q,
        "SELECT * FROM employees WHERE dept = '%s' AND salary >= %d" % (other, smin),
        "SELECT * FROM employees WHERE dept = '%s' AND salary < %d" % (dept, smin),
        "SELECT * FROM employees WHERE dept = '%s'" % dept,
    }
    opts = list(options)
    rng.shuffle(opts)
    letters = ["A", "B", "C", "D"]
    options_map = dict(zip(letters, opts))
    correct_option = letters[opts.index(ref_q)]
    return {
        "id": make_id(TYPE, seed),
        "type": TYPE,
        "difficulty": float(difficulty),
        "seed": int(seed),
        "prompt": ("Table employees(id, name, dept, salary) has %d rows, e.g. %s. "
                   "Departments: %s.\n"
                   "Exactly one of the following queries returns exactly %d rows. "
                   "Which one (A, B, C or D)?\n\n%s"
                   % (n, rows[:3], ", ".join(DEPTS), c_ref,
                      "\n\n".join("(%s) ```sql\n%s\n```" % (l, options_map[l])
                                  for l in letters))),
        "answer": {"correct_option": correct_option, "expected_rows": c_ref},
        "solution": ("Options give %d/%d/%d/%d rows respectively; only the reference "
                     "query matches %d rows."
                     % (c_ref, c_wrong, c_flip, c_miss, c_ref)),
        "meta": {"tables": {"employees": rows}, "options": options_map,
                 "expected_rows": c_ref},
    }


def verify(problem):
    try:
        conn = build_db(problem["meta"])
        matches = [opt for opt, q in problem["meta"]["options"].items()
                   if len(run_query(conn, q)) == problem["meta"]["expected_rows"]]
        conn.close()
        return (len(matches) == 1
                and matches[0] == problem["answer"]["correct_option"]
                and problem["answer"]["expected_rows"] == problem["meta"]["expected_rows"])
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
    p["answer"]["correct_option"] = ("A" if p["answer"]["correct_option"] != "A"
                                     else "B")
    cases.append(("verify-false-wrong-option", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["expected_rows"] += 1
    cases.append(("verify-false-wrong-expected", lambda p=p: verify(p) is False))
    p = copy.deepcopy(base)
    p["meta"]["options"][p["answer"]["correct_option"]] = \
        "SELECT * FROM employees WHERE salary > 999999999"
    cases.append(("verify-false-tampered-option", lambda p=p: verify(p) is False))
    from .common import schema_ok
    cases.append(("schema-ok", lambda: schema_ok(generate(42, 0.3))))
    def _counts_helper():
        rows = [(1, "a", "eng", 5000), (2, "b", "eng", 2000), (3, "c", "hr", 9000)]
        return _counts(rows, "eng", "hr", 3000) == (1, 1, 1, 2)
    cases.append(("counts-helper", _counts_helper))
    return cases
