# Evidence Model

Evidence is our most important primitive. Every finding accumulates evidence.

## Evidence Types
- **Data evidence:** null rate, distribution, row sample, duplicate pattern, outlier
- **Query evidence:** SQL result
- **Diff evidence:** before -> after
- **Code evidence:** commit changed line X
- **Pipeline evidence:** run failed, duration increased
- **Schema evidence:** INTEGER -> VARCHAR
- **Historical evidence:** same incident occurred 41 days ago

## Distinguish Facts from Inference
- **FACT:** 12,481 duplicate customer_id values exist.
- **EVIDENCE:** 96% of duplicate groups share the same ingestion_batch_id.
- **HYPOTHESIS:** The duplicates may originate from repeated ingestion batches.
- **CONFIDENCE:** 87%
- **VERIFIED?** No.

Every important system operation emits evidence.
