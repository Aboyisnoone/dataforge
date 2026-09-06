import duckdb
from typing import List, Dict, Any, Literal
from dataclasses import dataclass

from core.dataset import DatasetVersion
from core.semantics.models import ColumnSemantics
from core.semantics.classifier import SemanticClassifier
from core.findings.models import Observation, Finding, FindingCategory, Severity
from core.quality.severity import ImpactCalculator
from core.quality.applicability import RuleApplicability, ApplicabilityResult

from dataclasses import dataclass, field
from core.evidence.models import Evidence, EvidenceType

ResultStatus = Literal["passed", "failed", "unknown"]

@dataclass
class RuleResult:
    rule_name: str
    column: str
    status: ResultStatus
    observed_value: Any
    description: str
    query_used: str = ""

class BaseRule:
    def check_applicability(self, semantics: ColumnSemantics) -> ApplicabilityResult:
        raise NotImplementedError

    def evaluate(self, con: duckdb.DuckDBPyConnection, table_ref: str) -> RuleResult:
        raise NotImplementedError

class NotNullRule(BaseRule):
    def __init__(self, column: str):
        self.column = column
        
    def check_applicability(self, semantics: ColumnSemantics) -> ApplicabilityResult:
        return RuleApplicability.for_not_null_rule(semantics)
        
    def evaluate(self, con: duckdb.DuckDBPyConnection, table_ref: str) -> RuleResult:
        try:
            query = f"SELECT COUNT(*) FROM {table_ref} WHERE {self.column} IS NULL"
            res = con.execute(query).fetchone()
            null_count = res[0] if res else 0
            
            status: ResultStatus = "passed" if null_count == 0 else "failed"
            desc = "No nulls allowed" if null_count == 0 else f"Found {null_count} null values"
            
            return RuleResult(
                rule_name="NotNull",
                column=self.column,
                status=status,
                observed_value=null_count,
                description=desc,
                query_used=query
            )
        except Exception as e:
            return RuleResult("NotNull", self.column, "unknown", None, f"Evaluation failed: {e}")

class UniqueRule(BaseRule):
    def __init__(self, column: str):
        self.column = column
        
    def check_applicability(self, semantics: ColumnSemantics) -> ApplicabilityResult:
        return RuleApplicability.for_unique_rule(semantics)
        
    def evaluate(self, con: duckdb.DuckDBPyConnection, table_ref: str) -> RuleResult:
        try:
            query = f"""
                SELECT COUNT(*) as total, COUNT(DISTINCT {self.column}) as unique_count
                FROM {table_ref}
            """
            res = con.execute(query).fetchone()
            total = res[0]
            uniques = res[1]
            
            duplicates = total - uniques
            status: ResultStatus = "passed" if duplicates == 0 else "failed"
            desc = "All values are unique" if duplicates == 0 else f"Found {duplicates} duplicate records/groups"
            
            return RuleResult(
                rule_name="Unique",
                column=self.column,
                status=status,
                observed_value=duplicates,
                description=desc,
                query_used=query.strip()
            )
        except Exception as e:
            return RuleResult("Unique", self.column, "unknown", None, f"Evaluation failed: {e}")

class QualityEngine:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')
        self.classifier = SemanticClassifier()
        
    def evaluate_rules(self, version: DatasetVersion, rules: List[BaseRule]) -> List[Finding]:
        if not version.stats:
            raise ValueError("DatasetVersion must be profiled before quality evaluation")
            
        location = version.location
        if version.format == 'csv':
            table_ref = f"read_csv_auto('{location}')"
        elif version.format == 'parquet':
            table_ref = f"read_parquet('{location}')"
        else:
            raise ValueError(f"Unsupported format: {version.format}")
            
        findings = []
        total_rows = version.stats['row_count']
        
        # 1. Classify all columns
        semantics_map = {}
        for col_name, col_stats in version.stats['columns'].items():
            semantics_map[col_name] = self.classifier.classify(col_name, col_stats, total_rows)
            
        # 2. Evaluate rules
        for rule in rules:
            col_name = getattr(rule, 'column', None)
            if not col_name or col_name not in semantics_map:
                continue
                
            semantics = semantics_map[col_name]
            
            # Rule Applicability
            app_result = rule.check_applicability(semantics)
            if not app_result.applicable:
                continue # Skip suppressed rules
                
            # Execute
            result = rule.evaluate(self.con, table_ref)
            
            # Violation?
            if result.status == "failed":
                # Create Observation
                obs = Observation(
                    metric=f"{result.rule_name.lower()}_violation",
                    value=result.observed_value,
                    column=col_name,
                    dataset_version=version.version_id,
                    description=result.description
                )
                
                # Calculate Impact
                affected_fraction = 0.0
                if total_rows > 0:
                    try:
                        affected_fraction = float(result.observed_value) / total_rows
                    except:
                        pass
                
                rule_class_name = rule.__class__.__name__
                impact_res = ImpactCalculator.calculate(
                    rule_name=rule_class_name,
                    semantic_role=semantics.semantic_role,
                    affected_fraction=affected_fraction,
                    confidence=app_result.confidence
                )
                
                # Map category
                category = FindingCategory.UNKNOWN
                if result.rule_name == "Unique":
                    category = FindingCategory.UNIQUENESS
                elif result.rule_name == "NotNull":
                    category = FindingCategory.COMPLETENESS
                    
                finding = Finding(
                    title=f"Column '{col_name}' failed {result.rule_name} rule",
                    description=f"{result.description}. Context: {app_result.reason}",
                    category=category,
                    severity=impact_res.severity,
                    confidence=app_result.confidence,
                    impact_score=impact_res.impact_score,
                    column=col_name,
                    rule=rule_class_name,
                    observations=[obs]
                )
                
                # Generate Evidence
                ev_metric = Evidence(
                    type=EvidenceType.METRIC,
                    source=rule_class_name,
                    dataset_version=version.version_id,
                    metric="violation_count",
                    value=result.observed_value,
                    description=f"Observed {result.observed_value} violations"
                )
                finding.add_evidence(ev_metric)
                
                if result.query_used:
                    ev_query = Evidence(
                        type=EvidenceType.QUERY,
                        source=rule_class_name,
                        dataset_version=version.version_id,
                        metric="evaluation_query",
                        value=result.query_used,
                        description="SQL query used to detect the violation"
                    )
                    finding.add_evidence(ev_query)
                
                findings.append(finding)
                
        return findings
