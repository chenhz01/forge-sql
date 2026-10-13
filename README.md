# forge-sql

> **The database is the judge.** Text-to-SQL reasoning problems graded by running queries against a seeded in-memory SQLite database — result sets decide, not opinions.

Part of the [forge family](https://github.com/chenhz01/forge-kit): [scireason-forge](https://github.com/chenhz01/scireason-forge) · [forge-agentic](https://github.com/chenhz01/forge-agentic) · [forge-code](https://github.com/chenhz01/forge-code) · [forge-security](https://github.com/chenhz01/forge-security) · [forge-optimize](https://github.com/chenhz01/forge-optimize).

## Why this exists

Text-to-SQL is the #1 enterprise AI use case, and its benchmarks are frozen spreadsheets that everyone has memorized. Here the database is **reborn from a seed** for every exam: same seed, same data, byte-identical; new seed, a database that has never existed before. The grading authority is `sqlite3` itself — we run the queries and diff the result sets.

## Five task types (W1: 250 problems)

| Type | What it drills | Oracle |
|---|---|---|
| `select-filter` | WHERE clauses on a seeded table | Row count by execution |
| `aggregate-query` | GROUP BY + COUNT/SUM/AVG | Aggregates by execution |
| `join-query` | Two-table JOIN + HAVING | Result set by execution |
| `order-limit` | ORDER BY with deterministic tie-breaks | Top-k rows by execution |
| `query-debug` | Spot the query that returns the target | All candidates executed, exactly one matches |

## Quickstart

```bash
python cli.py generate --type all --per-type 50 --seed0 1000 --out data/w1.jsonl
python cli.py grade --file data/w1.jsonl        # SUMMARY: 250/250 passed
python self_test.py                             # SUMMARY: PASS 157/157
python -m bench.harness --file data/w1.jsonl --backend random   # chance: 0.0%
```

## When NOT to use

Natural-language-to-SQL *generation* benchmarks with open schemas (we grade closed-form reasoning on seeded data); production query linting.

## License & contact

MIT — © zhengming contributors. Developer tooling, not professional advice. Contact: hcac4735@agent.qq.com
