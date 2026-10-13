# -*- coding: utf-8 -*-
"""forge-sql: SQL reasoning graded by EXECUTION on a seeded SQLite database."""
MODULES = {}
for _name in ("select_filter", "aggregate_query", "join_query",
              "order_limit", "query_debug"):
    try:
        _m = __import__("forge." + _name, fromlist=["x"])
        MODULES[_m.TYPE] = _m
    except ImportError:
        pass
