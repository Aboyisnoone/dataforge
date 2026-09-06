# Roadmap

## Phase 0 - Research & Discovery (Weeks 1-2)
- Competitive teardown (Data Wrangler, OpenRefine, DuckDB, Great Expectations, Datafold, Soda, OpenMetadata, dbt Wizard).
- Customer discovery: 10-20+ interviews focusing on past data incidents.

## Phase 1 - Core Engine (Weeks 3-4)
- Technical spike: load, profile, fingerprint, diff, quality checks using DuckDB/Polars/PyArrow.
- Investigation prototype: ugly vertical slice of the core loop (upload -> profile -> detect -> investigate -> compare -> report).

## v0.1 - MVP (No AI)
- Local ingestion, Explorer, Profiler, Basic Quality Engine, SQL Lab, Diff, Investigation Workspace, Transformations, Export.

## v0.2 - Differentiation
- Investigation intelligence (anomaly prioritization, hypothesis object).
- Reproducibility (pipeline export, deterministic IDs).
- Dataset versions.
- Better diff (distributions, value-level).

## v0.3 - Developer Tooling
- CLI (`dataforge investigate`, etc.).
- Git integration (commit detection).
- CI (GitHub Action).

## v0.4 - AI
- Investigation Copilot using tools over evidence.

## v0.5 - Integrations
- DBs (Postgres, Snowflake, BigQuery), S3, dbt, Airflow.

## v1.0 - Collaborative
- Cloud workspace, RBAC, sharing.
