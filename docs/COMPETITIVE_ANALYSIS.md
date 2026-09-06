# Competitive Analysis

What we are deliberately taking from existing products. We refine them by integrating them into the investigation loop.

## Microsoft Data Wrangler
Take: Dataset table viewer, column stats, filtering, non-destructive editing, transformation history, generated code.
Refine: Transformation becomes part of an investigation (Why? What evidence? What changed? Validation rule?), not an isolated editing action.

## OpenRefine
Take: Faceted exploration, data cleaning, undo/redo, reproducible transformations.
Refine: Start from "Something deserves investigation" rather than "Help me clean my messy data". Every cleaning operation must have a machine-readable representation.

## DuckDB
Take: Analytical query engine, local execution, SQL.
Refine: DuckDB is the query execution layer. SQL results become promotable into evidence.

## Great Expectations
Take: Validation rules, historical validation.
Refine: Ask "What does the data tell us should probably be a rule?" rather than starting with rule writing.

## Datafold
Take: Row-level/schema diff, CI concept.
Refine: Add an impact layer. Does this difference matter? (e.g., revenue mean changed, rather than just 7 rows affected).

## Soda / Observability
Take: Anomaly detection, volume/completeness monitoring.
Refine: Alerts are starting points for investigation, providing context and possible related events.

## OpenMetadata / DataHub
Take: Lineage concepts, historical investigations.
Refine: We do NOT build a data catalog. Make lineage investigation-specific to reduce cognitive overload.

## dbt Wizard
Take: Investigation, root-cause analysis.
Refine: DataForge is data-source and workflow agnostic. Our initial unit is a data incident, not a dbt project.

## What we will deliberately NOT copy
- Enterprise observability
- Enterprise data catalog
- IDE data cleaning
- General-purpose data cleaning
- Data diff platform
- dbt-native AI agent
- BI platform
- Autonomous production remediation
