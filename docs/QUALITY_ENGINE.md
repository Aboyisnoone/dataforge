# Quality Engine

## Rule Types
- NotNullRule
- UniqueRule
- RangeRule
- RegexRule
- SetMembershipRule
- TypeRule
- SchemaRule
- FreshnessRule
- DistributionRule

Each returns: passed, failed, unknown. (Not just True/False, because data might be insufficient to decide).

## Findings vs. Rules
Transform raw checks into findings. A rule detects something; a finding puts it into context.
Rule: customer_id unique -> FAIL
Finding: Customer IDs contain duplicates (Severity: HIGH).

## Investigation to Validation
Observed behavior -> Suggested invariant -> Human approval -> Validation rule -> Future protection.
Export to Great Expectations, dbt tests, DataForge YAML.
