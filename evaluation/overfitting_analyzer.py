def detect_no_validation(code, file_path):
    has_fit = ".fit(" in code
    has_evaluation = any(pattern in code for pattern in [
        ".score(X_test", ".predict(X_test", ".evaluate(X_test",
        ".score(val", ".predict(val", ".evaluate(val",
    ])

    issues = []

    if has_fit and not has_evaluation:
        issues.append({
            "file": file_path,
            "issue": "Model is trained but never evaluated on a validation/test set",
            "severity": "medium",
            "suggestion": "Add a train/validation split and evaluate performance (e.g. accuracy, loss) on held-out data to check for overfitting.",
        })

    return issues


def scan_repository_for_overfitting_risk(files):
    all_issues = []

    for file in files:
        issues = detect_no_validation(
            file["code"],
            file["relative_path"],
        )
        all_issues.extend(issues)

    return all_issues


if __name__ == "__main__":
    risky_code = """
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
model.fit(X, y)
predictions = model.predict(X)
"""

    safe_code = """
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = LogisticRegression()
model.fit(X_train, y_train)
test_accuracy = model.score(X_test, y_test)
"""

    print("--- Risky code (should flag) ---")
    for issue in detect_no_validation(risky_code, "risky.py"):
        print(issue)

    print("\n--- Safe code (should show no issues) ---")
    safe_issues = detect_no_validation(safe_code, "safe.py")
    print(f"Issues found: {len(safe_issues)}")