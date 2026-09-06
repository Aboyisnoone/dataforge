# User Problems & Discovery

## Problem Patterns to Look For
- Data cleaning
- Data anomaly
- Schema drift
- Pipeline failure
- Unexpected output
- Duplicate records
- Missing data
- Metric regression

## Interview Questions for Discovery
- What happened?
- What was broken?
- How did you discover it?
- What tools did you use?
- What did you check first?
- How long did it take?
- What was the hardest part?
- What information was missing?
- What did you ultimately change?
- How did you verify the fix?
- Did you document the investigation?
- Did you create a test afterward?

## The Killer UX Flow
1. Upload yesterday.parquet and today.parquet
2. Comparison complete. 3 important changes found.
3. Click Investigate (e.g., revenue mean dropped).
4. DataForge gathers evidence (schema, distribution, SQL, etc.).
5. AI proposes Likely cause with confidence and evidence.
6. User tests hypothesis.
7. Generate fix (SQL/Python/validation).
