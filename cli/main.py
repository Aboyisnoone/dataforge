import argparse
import sys
import os

# Ensure core is in path for local execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.loader import load_dataset_version
from core.profiler import Profiler
from core.diff import DiffEngine
from core.quality.engine import QualityEngine, NotNullRule, UniqueRule
from core.investigation.models import Investigation, InvestigationStatus
from core.investigation.recommender import InvestigationRecommender

def run_profile(args):
    print(f"Profiling {args.file}...")
    try:
        version = load_dataset_version("dataset", args.file)
        profiler = Profiler()
        stats = profiler.profile(version.location, version.format)
        
        print("\n--- DATAFORGE ANALYSIS ---")
        print(f"Format: {version.format.upper()}")
        print(f"Rows: {stats['row_count']}")
        print(f"Columns: {len(stats['columns'])}")
        print("\nColumn Statistics:")
        for col_name, col_stats in stats['columns'].items():
            null_pct = col_stats['null_fraction'] * 100
            print(f"  - {col_name} ({col_stats['dtype']}): {col_stats['unique_count']} unique, {null_pct:.1f}% nulls")
            
    except Exception as e:
        print(f"Error profiling {args.file}: {e}")

def run_diff(args):
    print(f"Comparing {args.file_a} -> {args.file_b}...")
    try:
        version_a = load_dataset_version("dataset_a", args.file_a)
        version_b = load_dataset_version("dataset_b", args.file_b)
        
        profiler = Profiler()
        engine = DiffEngine(profiler)
        diff = engine.compare(version_a, version_b)
        
        print("\n--- DATAFORGE DIFF ---")
        print(f"Impact: {diff.impact_score}")
        print(f"Rows: {diff.row_diff.old_count} -> {diff.row_diff.new_count} ({diff.row_diff.diff_count:+d})")
        
        if diff.schema_diff.added_columns:
            print(f"Added Columns: {', '.join(diff.schema_diff.added_columns)}")
        if diff.schema_diff.removed_columns:
            print(f"Removed Columns: {', '.join(diff.schema_diff.removed_columns)}")
            
        print("\nColumn Changes:")
        for cd in diff.column_diffs:
            print(f"  - {cd.column_name}: Null fraction changed by {cd.null_fraction_change:+.1%}, Mean changed by {cd.mean_change:+.2f}")
            
    except Exception as e:
        print(f"Error diffing: {e}")

def run_investigate(args):
    print(f"Investigating {args.file}...\n")
    try:
        version = load_dataset_version("dataset", args.file)
        profiler = Profiler()
        version.stats = profiler.profile(version.location, version.format)
        
        inv = Investigation(
            title=f"CLI Investigation of {os.path.basename(args.file)}",
            description="Automated CLI investigation.",
            dataset_version=version.version_id,
            status=InvestigationStatus.OPEN
        )
        
        # Build rules for every column; Engine Applicability handles the filtering!
        rules = []
        for col in version.stats['columns'].keys():
            rules.append(NotNullRule(col))
            rules.append(UniqueRule(col))
            
        q_engine = QualityEngine()
        findings = q_engine.evaluate_rules(version, rules)
        inv.findings.extend(findings)
        
        # Sort by impact_score descending
        inv.findings.sort(key=lambda f: f.impact_score, reverse=True)
        
        print("DATAFORGE INVESTIGATION")
        print("--------------------------------")
        print(f"Dataset: {os.path.basename(args.file)}")
        print(f"Status:  {inv.status.value}")
        
        if not findings:
            print("\nNo findings detected.")
            return
            
        print("\nFINDINGS\n")
        
        severity_icons = {
            "CRITICAL": "!",
            "HIGH": "X",
            "MEDIUM": "-",
            "LOW": ".",
            "INFO": "i"
        }
        
        for f in inv.findings:
            icon = severity_icons.get(f.severity.value, " ")
            print(f"[{icon}] {f.severity.value}")
            print(f"{f.title}")
            
            violation_count = next((ev.value for ev in f.evidence if ev.metric == "violation_count"), None)
            if violation_count is not None and version.stats['row_count']:
                affected_pct = (float(violation_count) / version.stats['row_count']) * 100
                print(f"Affected: {affected_pct:.1f}%")
                
            print(f"Confidence: {f.confidence * 100:.0f}%")
            
            if args.explain:
                print(f"\nExplanation:")
                print(f"  {f.description}")
            
            if f.evidence:
                print("\nEvidence:")
                for ev in f.evidence:
                    print(f"  - [{ev.type.value}] {ev.description}")
                    if args.explain and ev.type.value == "QUERY":
                        print(f"    SQL: {ev.value}")
                        
            actions = InvestigationRecommender.recommend(f)
            if actions:
                print("\nSuggested next steps:")
                for i, action in enumerate(actions, 1):
                    print(f"  {i}. [{action.type}] {action.rationale}")
            
            print("\n--------------------------------\n")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error investigating {args.file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="DataForge CLI - Debug your data.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    profile_parser = subparsers.add_parser("profile", help="Profile a dataset")
    profile_parser.add_argument("file", help="Path to CSV or Parquet file")
    
    diff_parser = subparsers.add_parser("diff", help="Compare two datasets")
    diff_parser.add_argument("file_a", help="Path to original file")
    diff_parser.add_argument("file_b", help="Path to new file")
    
    inv_parser = subparsers.add_parser("investigate", help="Run automated investigation on a dataset")
    inv_parser.add_argument("file", help="Path to CSV or Parquet file")
    inv_parser.add_argument("--explain", action="store_true", help="Show detailed explanation of findings")
    
    args = parser.parse_args()
    
    if args.command == "profile":
        run_profile(args)
    elif args.command == "diff":
        run_diff(args)
    elif args.command == "investigate":
        run_investigate(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
