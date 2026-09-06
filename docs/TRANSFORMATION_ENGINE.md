# Transformation Engine

Transformations must be investigation-aware and reversible where practical.

## Object Representation
- type (e.g., normalize_category)
- parameters
- input fingerprint
- output fingerprint
- timestamp
- affected columns
- affected row estimate
- generated code

## Validation After Transformation
Every transformation triggers:
- Re-profile
- Re-run affected validations
- Compare statistics
- Check schema & row counts
- Check unintended changes

## Before / After
Never silently modify data. Show BEFORE and AFTER states, highlighting unintended changes to establish trust.
