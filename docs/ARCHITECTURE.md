# Architecture

## Local-first Architecture
Default: No data upload. Processing happens locally.
- **Frontend:** React + TypeScript
- **Backend:** FastAPI (Python)
- **Data Processing:** Polars
- **SQL Engine:** DuckDB
- **File Format Layer:** PyArrow
- **Local Persistence:** SQLite
- **API:** REST initially
- **Background Execution:** Python worker initially

## Internal Domains
`backend/`
├── `api/`
├── `investigations/`
├── `datasets/`
├── `profiler/`
├── `diff/`
├── `quality/`
├── `transformations/`
├── `evidence/`
├── `hypotheses/`
├── `validation/`
├── `lineage/`
├── `ai/`
├── `codegen/`
└── `integrations/`

## Core Entities (Internal Data Model)
Workspace, Dataset, DatasetVersion, Investigation, Finding, Evidence, Hypothesis, Query, Transformation, ValidationRule, ValidationRun, Diff, Artifact, Integration.
