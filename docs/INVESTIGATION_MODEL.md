# Investigation Model

Every investigation should have a stable structure. This is the internal backbone.

## The Investigation Object
- Title
- Description
- Status
- Severity
- Started At
- Dataset(s)
- Finding(s)
- Evidence
- Hypotheses
- Queries
- Transformations
- Validation rules
- Diff results
- Generated artifacts
- Timeline
- Resolution

## Dataset Versions
Datasets are versioned (v001, v002, etc.). Each version contains fingerprint, schema, stats, location, created_at, source. This unlocks diffing and historical investigation.

## Investigation History
Past investigations become institutional memory. DataForge can surface: "A similar investigation occurred on July 14. Resolution: latest-record deduplication."
