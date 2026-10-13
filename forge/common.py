# -*- coding: utf-8 -*-
"""forge.common — shared schema for forge-sql task generators.

Domain: SQL reasoning graded by EXECUTION — a seeded in-memory SQLite
database is rebuilt from meta, and queries are actually run. Same seed ->
same database -> same query results.
"""
import hashlib
import sqlite3

TYPES = ("select-filter", "aggregate-query", "join-query", "order-limit",
         "query-debug")

_SCHEMA_KEYS = ("id", "type", "difficulty", "seed", "prompt", "answer",
                "solution", "meta")


def make_id(task_type, seed):
    h = hashlib.sha1(("%s|%d" % (task_type, seed)).encode("utf-8")).hexdigest()[:10]
    return "%s-%s" % (task_type, h)


def schema_ok(problem):
    if not isinstance(problem, dict):
        return False
    for k in _SCHEMA_KEYS:
        if k not in problem:
            return False
    if problem["type"] not in TYPES:
        return False
    if not (0.0 <= float(problem["difficulty"]) <= 1.0):
        return False
    for k in ("prompt", "solution"):
        if not isinstance(problem[k], str) or len(problem[k]) < 10:
            return False
    if not isinstance(problem["answer"], dict) or not problem["answer"]:
        return False
    if not isinstance(problem["meta"], dict):
        return False
    return True


def knob(difficulty, lo, hi):
    difficulty = min(max(difficulty, 0.0), 1.0)
    return lo + (hi - lo) * difficulty


def int_knob(difficulty, lo, hi):
    return int(round(knob(difficulty, lo, hi)))


TABLE_SPECS = {
    "employees": ("id INTEGER, name TEXT, dept TEXT, salary INTEGER",
                  ["id", "name", "dept", "salary"]),
    "orders": ("id INTEGER, emp_id INTEGER, amount INTEGER",
               ["id", "emp_id", "amount"]),
    "products": ("id INTEGER, category TEXT, price INTEGER",
                 ["id", "category", "price"]),
}

DEPTS = ["eng", "sales", "hr"]
CATEGORIES = ["tools", "books", "toys"]


def build_db(meta):
    """Rebuild the seeded in-memory database from meta["tables"]."""
    conn = sqlite3.connect(":memory:")
    for tname, rows in meta["tables"].items():
        cols_sql, _ = TABLE_SPECS[tname]
        conn.execute("CREATE TABLE %s (%s)" % (tname, cols_sql))
        ph = ",".join("?" * len(TABLE_SPECS[tname][1]))
        conn.executemany("INSERT INTO %s VALUES (%s)" % (tname, ph), rows)
    conn.commit()
    return conn


def run_query(conn, sql):
    """Execute and return a deterministic sorted list of rows."""
    cur = conn.execute(sql)
    return sorted([tuple(r) for r in cur.fetchall()])
