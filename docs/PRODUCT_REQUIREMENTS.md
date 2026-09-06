# Product Requirements

## Build Priority Stack
1. **P0 - Investigation correctness:** The system must produce reliable findings.
2. **P1 - Evidence quality:** The user must be able to understand why.
3. **P2 - Speed:** Investigation should feel substantially faster than doing it manually.
4. **P3 - Reproducibility:** Every accepted fix becomes reusable engineering output.
5. **P4 - Integrations:** Connect into the user's existing stack.
6. **P5 - AI:** Make existing workflows faster.
7. **P6 - Collaboration:** Only after usage validates the need.

## MVP Scope (v0.1)
- Data ingestion: CSV, Parquet, JSON, Excel
- Explorer: table view, filtering, sorting, column stats
- Profiler: row count, nulls, distinct, types, stats
- Basic quality engine: nullability, uniqueness, ranges, duplicates
- SQL Lab: DuckDB editor
- Diff: schema, row count, column stats, keyed row diff
- Investigation: findings, evidence, queries, notes, timeline
- Transformations: basic cleaning, preview, undo
- Export: cleaned dataset, SQL, Python, JSON report
*No AI yet.*
