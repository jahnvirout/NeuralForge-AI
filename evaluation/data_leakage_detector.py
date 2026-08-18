import re


def detect_scaling_before_split(code, file_path):
    """
    Checks if fit_transform (scaling/encoding) happens BEFORE train_test_split
    in the same file — a common data leakage mistake.
    """
    lines = code.split("\n")

    fit_transform_line = None
    split_line = None

    for i, line in enumerate(lines):
        if "fit_transform(" in line and fit_transform_line is None:
            fit_transform_line = i

        if "train_test_split(" in line and "import" not in line and split_line is None:
            split_line = i

    issues = []

    if fit_transform_line is not None and split_line is not None:
        if fit_transform_line < split_line:
            issues.append({
                "file": file_path,
                "issue": "Possible data leakage: fit_transform() called before train_test_split()",
                "line": fit_transform_line + 1,
                "severity": "high",
                "suggestion": "Split data first, then fit_transform only on training data.",
            })

    return issues


def scan_repository_for_leakage(files):
    """
    Runs the leakage check across all files in a repository.
    'files' comes from parse_repository() — full file data, not chunks.
    """
    all_issues = []

    for file in files:
        issues = detect_scaling_before_split(file["code"], file["relative_path"])
        all_issues.extend(issues)

    return all_issues

if __name__ == "__main__":
    sample_code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test = train_test_split(X_scaled, y, test_size=0.2)
"""

    issues = detect_scaling_before_split(sample_code, "bad_example.py")

    for issue in issues:
        print(issue)

    good_code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
"""

    print("\n--- Testing clean code (should show no issues) ---")
    clean_issues = detect_scaling_before_split(good_code, "good_example.py")
    print(f"Issues found: {len(clean_issues)}")