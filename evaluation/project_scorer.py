from evaluation.data_leakage_detector import scan_repository_for_leakage
from evaluation.overfitting_analyzer import scan_repository_for_overfitting_risk


def score_project(files):
    """
    Runs all available checks on a repository's files and produces
    an overall score (out of 100) plus a breakdown of findings.
    """
    leakage_issues = scan_repository_for_leakage(files)
    overfitting_issues = scan_repository_for_overfitting_risk(files)

    score = 100

    # Deduct points based on severity
    for issue in leakage_issues:
        if issue["severity"] == "high":
            score -= 15
        else:
            score -= 5

    for issue in overfitting_issues:
        if issue["severity"] == "high":
            score -= 15
        else:
            score -= 5

    score = max(score, 0)  # never go below 0

    report = {
        "overall_score": score,
        "total_issues": len(leakage_issues) + len(overfitting_issues),
        "data_leakage_issues": leakage_issues,
        "overfitting_risk_issues": overfitting_issues,
    }

    return report


def print_report(report):
    print(f"\nOverall Project Score: {report['overall_score']}/100")
    print(f"Total Issues Found: {report['total_issues']}\n")

    if report["data_leakage_issues"]:
        print("Data Leakage Issues:")
        for issue in report["data_leakage_issues"]:
            print(f"  - [{issue['file']}] Line {issue['line']}: {issue['issue']}")

    if report["overfitting_risk_issues"]:
        print("\nOverfitting Risk Issues:")
        for issue in report["overfitting_risk_issues"]:
            print(f"  - [{issue['file']}]: {issue['issue']}")

    if report["total_issues"] == 0:
        print("No issues found. Clean project!")


if __name__ == "__main__":
    from parser.repository_parser import parse_repository

    repo_path = input("Enter repository path: ")
    files = parse_repository(repo_path)

    report = score_project(files)
    print_report(report)