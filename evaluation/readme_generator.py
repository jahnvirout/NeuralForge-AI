from datetime import datetime


def generate_ml_report(files, chunks, score_report):
    """
    Generates a readable Markdown report summarizing the repository's
    structure and ML-specific findings.
    """
    lines = []

    lines.append(f"# ML Project Health Report")
    lines.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    lines.append(f"\n## Overview")
    lines.append(f"- Total files analyzed: {len(files)}")
    lines.append(f"- Total code chunks (functions/classes): {len(chunks)}")
    lines.append(f"- Overall Project Score: **{score_report['overall_score']}/100**")
    lines.append(f"- Total issues found: {score_report['total_issues']}")

    lines.append(f"\n## Findings")

    if score_report["data_leakage_issues"]:
        lines.append(f"\n### Data Leakage ({len(score_report['data_leakage_issues'])} issue(s))")
        for issue in score_report["data_leakage_issues"]:
            lines.append(f"- **{issue['file']}** (line {issue['line']}): {issue['issue']}")
            lines.append(f"  - *Suggestion:* {issue['suggestion']}")

    if score_report["overfitting_risk_issues"]:
        lines.append(f"\n### Overfitting Risk ({len(score_report['overfitting_risk_issues'])} issue(s))")
        for issue in score_report["overfitting_risk_issues"]:
            lines.append(f"- **{issue['file']}**: {issue['issue']}")
            lines.append(f"  - *Suggestion:* {issue['suggestion']}")

    if score_report["hyperparameter_issues"]:
        lines.append(f"\n### Hyperparameter Risk ({len(score_report['hyperparameter_issues'])} issue(s))")
        for issue in score_report["hyperparameter_issues"]:
            lines.append(f"- **{issue['file']}**: {issue['issue']}")
            lines.append(f"  - *Suggestion:* {issue['suggestion']}")

    if score_report["total_issues"] == 0:
        lines.append("\nNo issues found. This project follows good ML engineering practices.")

    return "\n".join(lines)


if __name__ == "__main__":
    from parser.repository_parser import parse_repository
    from parser.repo_chunker import chunk_repository
    from evaluation.project_scorer import score_project

    repo_path = input("Enter repository path: ")

    files = parse_repository(repo_path)
    chunks = chunk_repository(repo_path)
    score_report = score_project(files)

    report_text = generate_ml_report(files, chunks, score_report)

    print(report_text)

    with open("ml_project_report.md", "w") as f:
        f.write(report_text)

    print("\n\nReport saved to ml_project_report.md")