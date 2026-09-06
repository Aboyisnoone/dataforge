# AI Design

AI is introduced in v0.4 (Investigation Copilot, SQL Copilot, Validation Copilot, etc.).

## AI Grounding
The AI should never simply receive: "Analyze this dataset."
It receives structured Evidence, Findings, Schema, Diffs, Lineage, and Tool calls (inspect_column, run_sql, compare_dataset, propose_fix).
The model reasons over structured evidence, rather than hallucinating over raw data.

## Restrictions
- **No arithmetic:** AI should never be responsible for arithmetic. Calculate deterministically, then let the LLM interpret.
- **No silent destruction:** AI should never silently execute destructive actions. User must explicitly approve.
- **Facts vs. Speculation:** The system must clearly distinguish Observed, Inferred, Suggested, and Validated.
