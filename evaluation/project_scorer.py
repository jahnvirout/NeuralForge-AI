from typing import Any, Dict, List, Optional
from evaluation.data_leakage_detector import scan_repository_for_leakage
from evaluation.overfitting_analyzer import scan_repository_for_overfitting_risk
from evaluation.hyperparameter_analyzer import scan_repository_for_hyperparameter_risk

# Explicit, explainable rule weights — no hidden scoring factors
SCORING_RULES = {
    "data_leakage": {
        "rule_name": "Data Leakage Prevention",
        "points_per_issue": 15,
        "max_deduction": 45,
        "description": "Detects preprocessors fitted prior to dataset splitting.",
    },
    "overfitting_risk": {
        "rule_name": "Validation & Generalization Check",
        "points_per_issue": 10,
        "max_deduction": 30,
        "description": "Detects models trained without held-out test/validation evaluation.",
    },
    "hyperparameter_risk": {
        "rule_name": "Tree Complexity Constraints",
        "points_per_issue": 5,
        "max_deduction": 25,
        "description": "Detects tree models instantiated without max_depth or leaf constraints.",
    },
    "committed_dataset": {
        "rule_name": "Dataset Versioning Hygiene",
        "points_per_issue": 5,
        "max_deduction": 15,
        "description": "Detects raw datasets and large binaries committed directly to git.",
    },
}


def score_project(files: List[Dict[str, Any]], repo_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates ML repository hygiene across all detectors and computes an explainable health score.
    Returns full issue details, summary counts, committed dataset findings, and an itemized score breakdown.
    """
    leakage_issues = scan_repository_for_leakage(files)
    overfitting_issues = scan_repository_for_overfitting_risk(files)
    hyperparameter_issues = scan_repository_for_hyperparameter_risk(files)

    committed_dataset_issues: List[Dict[str, Any]] = []
    if repo_path:
        from parser.repository_parser import scan_committed_data_files
        raw_data_files = scan_committed_data_files(repo_path)
        for df in raw_data_files:
            committed_dataset_issues.append({
                "file": df["file"],
                "function": "<repository>",
                "line": 1,
                "start_line": 1,
                "end_line": 1,
                "severity": "medium",
                "issue": f"Skipped: dataset files committed to repo ({df['size_mb']} MB)",
                "why_it_matters": (
                    "Committing large datasets or binaries directly to git bloats clone sizes, "
                    "slows CI/CD, and violates ML versioning best practices."
                ),
                "evidence_snippet": f"{df['file']} ({df['size_bytes']:,} bytes)",
                "suggestion": "Track large datasets and model weights using DVC, S3, or Git LFS, and exclude them via .gitignore.",
                "confidence": "high",
            })

    leak_cfg = SCORING_RULES["data_leakage"]
    overfit_cfg = SCORING_RULES["overfitting_risk"]
    hyper_cfg = SCORING_RULES["hyperparameter_risk"]
    dataset_cfg = SCORING_RULES["committed_dataset"]

    leakage_deduction = min(len(leakage_issues) * leak_cfg["points_per_issue"], leak_cfg["max_deduction"])
    overfitting_deduction = min(len(overfitting_issues) * overfit_cfg["points_per_issue"], overfit_cfg["max_deduction"])
    hyperparam_deduction = min(len(hyperparameter_issues) * hyper_cfg["points_per_issue"], hyper_cfg["max_deduction"])
    dataset_deduction = min(len(committed_dataset_issues) * dataset_cfg["points_per_issue"], dataset_cfg["max_deduction"])

    total_deductions = leakage_deduction + overfitting_deduction + hyperparam_deduction + dataset_deduction
    overall_score = max(0, 100 - total_deductions)

    score_breakdown = [
        {
            "category": "data_leakage",
            "rule": leak_cfg["rule_name"],
            "points_deducted": leakage_deduction,
            "issues_count": len(leakage_issues),
            "max_deduction": leak_cfg["max_deduction"],
            "description": leak_cfg["description"],
        },
        {
            "category": "overfitting_risk",
            "rule": overfit_cfg["rule_name"],
            "points_deducted": overfitting_deduction,
            "issues_count": len(overfitting_issues),
            "max_deduction": overfit_cfg["max_deduction"],
            "description": overfit_cfg["description"],
        },
        {
            "category": "hyperparameter_risk",
            "rule": hyper_cfg["rule_name"],
            "points_deducted": hyperparam_deduction,
            "issues_count": len(hyperparameter_issues),
            "max_deduction": hyper_cfg["max_deduction"],
            "description": hyper_cfg["description"],
        },
    ]
    if committed_dataset_issues:
        score_breakdown.append({
            "category": "committed_dataset",
            "rule": dataset_cfg["rule_name"],
            "points_deducted": dataset_deduction,
            "issues_count": len(committed_dataset_issues),
            "max_deduction": dataset_cfg["max_deduction"],
            "description": dataset_cfg["description"],
        })

    report = {
        "overall_score": overall_score,
        "total_issues": (
            len(leakage_issues)
            + len(overfitting_issues)
            + len(hyperparameter_issues)
            + len(committed_dataset_issues)
        ),
        "data_leakage_issues": leakage_issues,
        "overfitting_risk_issues": overfitting_issues,
        "hyperparameter_issues": hyperparameter_issues,
        "committed_dataset_issues": committed_dataset_issues,
        "score_breakdown": score_breakdown,
    }

    return report


def print_report(report: Dict[str, Any]) -> None:
    """Helper to display score report on CLI."""
    print(f"\nOverall Project Score: {report['overall_score']}/100")
    print(f"Total Issues Found: {report['total_issues']}\n")

    print("Score Breakdown:")
    for item in report.get("score_breakdown", []):
        print(f"  - {item['rule']}: -{item['points_deducted']} pts ({item['issues_count']} issue(s))")

    if report.get("data_leakage_issues"):
        print("\nData Leakage Issues:")
        for issue in report["data_leakage_issues"]:
            print(f"  - [{issue['file']}] Line {issue['line']}: {issue['issue']}")

    if report.get("overfitting_risk_issues"):
        print("\nOverfitting Risk Issues:")
        for issue in report["overfitting_risk_issues"]:
            print(f"  - [{issue['file']}]: {issue['issue']}")

    if report.get("hyperparameter_issues"):
        print("\nHyperparameter Risk Issues:")
        for issue in report["hyperparameter_issues"]:
            print(f"  - [{issue['file']}]: {issue['issue']}")

    if report.get("committed_dataset_issues"):
        print("\nCommitted Dataset Issues:")
        for issue in report["committed_dataset_issues"]:
            print(f"  - [{issue['file']}]: {issue['issue']}")

    if report["total_issues"] == 0:
        print("\nNo issues found. Clean project!")


if __name__ == "__main__":
    from parser.repository_parser import parse_repository

    repo_path = input("Enter repository path: ")
    files = parse_repository(repo_path)
    report = score_project(files, repo_path=repo_path)
    print_report(report)