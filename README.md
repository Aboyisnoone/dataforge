# DataForge

An automated data quality and investigation platform powered by deterministic profiling and AI-driven synthesis.

[Live Demo] | [GitHub] | [Documentation] | [Demo Video]

## ?? What is DataForge?

DataForge is a platform designed to treat data anomalies like software incidents. Instead of just flagging a "data quality failure," DataForge tracks dataset versions, deterministically diffs their statistical profiles, automatically hypothesizes root causes, and validates those theories using sandboxed SQL experiments. 

## ?? The Problem

Modern data pipelines fail silently. When a downstream dashboard breaks, data engineers spend hours manually querying historical partitions, writing ad-hoc diffing scripts, and guessing what changed upstream. Current tools tell you *that* data broke (e.g., "null rate > 5%"), but they don't tell you *why* or build a reproducible investigation.

## ? Key Features

- **Immutable Dataset Versioning**: Upload CSV, JSON, or Parquet files and track chronological changes.
- **Deterministic Diffing**: Polars-powered statistical profiling automatically detects schema shifts, null explosions, and cardinality changes between versions.
- **AI Hypothesis Synthesis**: Gemini Copilot analyzes the diff and generates plausible root cause theories.
- **Sandboxed SQL Experiments**: Prove hypotheses by executing read-only, sandboxed SQLite queries against the data.
- **Historical Memory**: Resolutions are stored as immutable precedent. Future investigations retrieve past resolutions when similar anomalies occur.
- **Multi-tenant Architecture**: Full workspace isolation and containerized deployment.

## ?? Core Architecture

`mermaid
graph TD
    A[Data Ingestion] -->|Polars Profiling| B(Dataset Versions)
    B -->|Diff Engine| C{Quality Engine}
    C -->|Evidence| D[Findings]
    D --> E[Hypothesis Synthesis]
    E --> F[SQL Sandbox Experiments]
    F -->|Validation| G[Root Cause Candidate]
    G --> H[Human Resolution]
    H --> I[(Historical Memory)]
`

## ?? Deterministic Truth vs AI Interpretation

DataForge maintains a strict boundary:
- **Truth** comes from deterministic engines (Polars profiling, SQLite queries).
- **Interpretation** is handled by AI (Gemini).
- **Authority** remains with the human engineer.
- **Proof** is generated through isolated experiments.
- **Context** is retrieved from historical memory.

## ?? How an Investigation Works

1. **Ingest**: A new version of a dataset is uploaded.
2. **Detect**: The Diff Engine compares it against the previous version.
3. **Attribute**: Changes are flagged as Findings (e.g., Uniqueness drop).
4. **Hypothesize**: AI generates candidate theories.
5. **Experiment**: Sandboxed SQL queries run to validate the theories.
6. **Resolve**: The engineer reviews the evidence and confirms a resolution.
7. **Remember**: The resolution is saved to assist future identical incidents.

## ??? Screenshots / Demo

*(Coming Soon - Screenshots of the React Investigation Workbench)*

## ??? Tech Stack

- **Backend**: FastAPI (Python), DuckDB/Polars, SQLite (Sandboxing), SQLAlchemy
- **Frontend**: React, Vite, Tailwind CSS
- **AI / LLM**: Google Gemini API, Tenacity (Resilience)
- **Infrastructure**: Docker Compose, PostgreSQL (Persistence), MinIO (S3 Object Storage)

## ?? Getting Started

### Prerequisites
- Docker & Docker Compose
- A Google Gemini API Key

### Environment Variables
Copy the configuration template:
\\\ash
cp .env.example .env
\\\
Edit \.env\ and insert your \GEMINI_API_KEY\.

### Docker Setup
We use Docker Compose to orchestrate the entire multi-container stack.
\\\ash
docker compose up -d --build
\\\

- **Frontend**: http://localhost:5180
- **API**: http://localhost:8000
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)

### Running Locally
To run without Docker:
\\\ash
cd backend
pip install -r requirements.txt
uvicorn backend.api.main:app --reload

cd frontend
npm install
npm run dev
\\\

## ?? How to Use DataForge

### 1. Create an account
*(Not required in v1.1 - Local Workspace isolation handles multi-tenancy)*

### 2. Upload dataset
Upload a base \.csv\, \.parquet\, or \.json\ file via the UI.

### 3. Create a new version
Upload a modified version of the same dataset.

### 4. Investigate findings
The Diff Engine will highlight schema and statistical changes.

### 5. Review evidence
View the exact metrics that drifted between versions.

### 6. Run an experiment
Use the SQL Sandbox to query the dataset and prove why the data drifted.

### 7. Ask Copilot
Chat with the Gemini Copilot, grounded entirely in the deterministic facts of the investigation.

### 8. Resolve investigation
Mark the investigation as resolved to persist it into Historical Memory.

## ??? Project Structure

\\\
.
+-- backend/               # FastAPI application
¦   +-- api/               # API Routes & Middleware
¦   +-- copilot/           # Gemini AI Integration & Context Building
¦   +-- persistence/       # PostgreSQL Repositories
+-- core/                  # Core Business Logic (Framework Agnostic)
¦   +-- diff.py            # Statistical Diff Engine
¦   +-- profiler.py        # Polars Profiling
¦   +-- execution/         # SQLite SQL Sandbox
+-- frontend/              # React UI
+-- scripts/               # CI/CD and E2E Testing Scripts
+-- docker-compose.yml     # Infrastructure Orchestration
+-- test_e2e.py            # End-to-End Validation
\\\

## ?? Testing & Validation

Run the automated E2E test script to ensure the deployed stack is healthy and operational:
\\\ash
python scripts/run_production_e2e.py
\\\

## ?? Security

- **Multi-Tenancy**: Workspace isolation across all endpoints.
- **Sandboxed SQL**: Destructive queries (\INSERT\, \DROP\, etc.) are actively blocked by SQLite \set_authorizer\.
- **Upload Limits**: In-memory chunk limits prevent OOM attacks during ingestion.
- **Prompt Safety**: Gemini API safety thresholds block dangerous output generation.

## ?? Development Journey

### Phase 1 — Quality Engine
Implemented Polars-based statistical profiling and historical diffing.
### Phase 2 — Context & Discovery
Built the Finding and Evidence generation mechanics.
### Phase 3 — Investigation Engine
Formalized Hypothesis models and status transitions.
### Phase 4 — Resolution & Lineage
Added root cause candidate ranking and investigation closure.
### Phase 5 — System Architecture
Re-architected to enforce the Truth vs. Interpretation boundary.
### Phase 6 — AI Integration
Introduced the Gemini Copilot and Context Builders.
### Phase 7 — Execution Environment
Built the secure SQL Sandbox for experimentation.
### Phase 8 — React Workbench
Developed the Frontend UI.
### Phase 9 — Historical Memory
Persisted resolutions as precedent for future Copilot retrieval.
### Phase 10 — Validation
Automated E2E deterministic verification.
### Phase 11 — Production Productization
Dockerization, PostgreSQL, MinIO, Telemetry, and CI/CD pipelines.

## ?? Known Limitations

- E2E tests currently bypass Gemini integration via dummy keys to ensure deterministic CI runs.
- Historical Memory retrieval is basic and relies on exact textual metadata rather than semantic vector search.

## ??? Roadmap

- **Phase 12**: Multi-Dataset Lineage & Cross-Dataset Investigation
- **Phase 13**: Vector-based Semantic Memory Retrieval
- **Phase 14**: Cloud IAM Integration

## ?? Contributing
Contributions are welcome. Please ensure \python scripts/run_production_e2e.py\ passes before submitting a Pull Request.

## ?? License
MIT License
