# Diff Engine

Our diff should answer: "Does this difference matter?" not only "What changed?".

## Supported Diff Levels (V1)
- **Dataset-level:** row counts, column counts, schemas
- **Column-level:** type changes, null percentage, uniqueness, cardinality, min/max, mean/median, quantiles
- **Value-level:** added/removed/modified rows (requires trustworthy key)
- **Distribution-level:** frequency changes, distribution shifts

## Impact Estimation
The key concept is impact, not difference. 7 rows affected in a status column vs. revenue mean dropping by 30% across 2.4 million rows. Impact scoring prioritizes findings (🔴 Critical, 🟠 Warning, 🟡 Informational).
