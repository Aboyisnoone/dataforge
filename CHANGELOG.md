# Changelog

## [1.1.0] - 2026-09-06

### Added
- **Multi-tenant Workspace Isolation**: Complete data and investigation separation via Workspace-Id header.
- **Production Storage Backend**: Replaced local file storage with S3/MinIO for datasets and PostgreSQL for structured investigation data.
- **Docker Containerization**: Full docker-compose.yml for standing up the API, Frontend, PostgreSQL, and MinIO in an isolated environment.
- **CI/CD Pipeline**: Added GitHub Actions workflow (.github/workflows/ci.yml) to automatically build images and verify E2E deployment.
- **Observability**: Centralized structured JSON logging and telemetry middleware for route latencies, dataset ingestion metrics, and Copilot token usage.
- **Security Hardening**:
  - Sandboxed SQLite execution using set_authorizer to block all destructive queries (INSERT/UPDATE/DELETE/DROP).
  - Configured strict chunked upload limits (MAX_UPLOAD_SIZE_BYTES) preventing OOM conditions.
  - Hardened API with strict CORS origins (ALLOWED_ORIGINS).
  - Added Gemini API safety settings to prevent prompt injection and block dangerous content generation.
  - Implemented slowapi rate limiting on FastAPI routes.

### Changed
- Centralized all environment variables and secrets management via pydantic-settings in core/config.py.
- Upgraded the profiling engine to Polars 1.44.1 for faster out-of-core schema extraction.
- Refactored Profile and ColumnProfile domain models to support rich dictionaries of column statistics instead of lists.

### Fixed
- Fixed cascading failures in E2E tests related to domain model divergence.
- Fixed 	enacity and duckdb dependencies missing from equirements.txt.
