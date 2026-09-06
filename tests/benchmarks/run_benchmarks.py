import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import polars as pl
from core.loader import load_dataset_version
from core.profiler import Profiler
from core.quality.engine import QualityEngine, UniqueRule, NotNullRule
from core.findings.models import Severity

def run_benchmark():
    engine = QualityEngine()
    profiler = Profiler()
    
    rules = [
        UniqueRule("customer_id"), UniqueRule("revenue"), UniqueRule("status_code"),
        NotNullRule("customer_id"), NotNullRule("revenue"), NotNullRule("status_code")
    ]
    
    datasets = {
        "A_Duplicate_PK": {
            "df": pl.DataFrame({"customer_id": [1, 2, 3, 3], "revenue": [10.0, 20.0, 30.0, 40.0]}),
            "expected_findings": 1,
            "expected_high_severity": 1,
            "is_negative_control": False
        },
        "B_Null_Explosion": {
            "df": pl.DataFrame({"customer_id": [1, 2, 3, 4], "revenue": [10.0, None, None, None]}),
            "expected_findings": 1,
            "expected_high_severity": 0,
            "is_negative_control": False
        },
        "K_Legitimate_Duplicates": {
            "df": pl.DataFrame({"customer_id": [1, 2, 3, 4], "revenue": [9.99, 9.99, 9.99, 19.99]}),
            "expected_findings": 0,
            "expected_high_severity": 0,
            "is_negative_control": True
        }
    }
    
    metrics = {
        "true_positives": 0,
        "false_positives": 0,
        "high_severity_false_positives": 0,
        "false_negatives": 0,
        "evidence_generated": 0,
        "total_expected": 0,
        "total_negative_controls": 0
    }
    
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for name, spec in datasets.items():
            filepath = os.path.join(tmpdir, f"{name}.csv")
            spec["df"].write_csv(filepath)
            
            version = load_dataset_version(name, filepath)
            version.stats = profiler.profile(version.storage_path, version.format)
            
            findings = engine.evaluate_rules(version, rules)
            
            if spec["is_negative_control"]:
                metrics["total_negative_controls"] += 1
                if len(findings) > 0:
                    metrics["false_positives"] += len(findings)
                    for f in findings:
                        if f.severity in (Severity.HIGH, Severity.CRITICAL):
                            metrics["high_severity_false_positives"] += 1
            else:
                metrics["total_expected"] += spec["expected_findings"]
                if len(findings) >= spec["expected_findings"]:
                    metrics["true_positives"] += spec["expected_findings"]
                else:
                    metrics["false_negatives"] += (spec["expected_findings"] - len(findings))
                    
            for f in findings:
                if f.evidence:
                    metrics["evidence_generated"] += 1
                    
    # Generate report
    total_positives = metrics["true_positives"] + metrics["false_negatives"]
    detection_acc = (metrics["true_positives"] / total_positives * 100) if total_positives else 100
    
    total_findings = metrics["true_positives"] + metrics["false_positives"]
    evidence_completeness = (metrics["evidence_generated"] / total_findings * 100) if total_findings else 100
    
    print("\nDATAFORGE BENCHMARK")
    print("--------------------------------")
    print(f"Detection Accuracy:            {detection_acc:.0f}%")
    print(f"False Positives:               {metrics['false_positives']}")
    print(f"High-Severity False Positives: {metrics['high_severity_false_positives']}")
    print(f"Evidence Completeness:         {evidence_completeness:.0f}%")
    print("--------------------------------\n")

if __name__ == "__main__":
    run_benchmark()
