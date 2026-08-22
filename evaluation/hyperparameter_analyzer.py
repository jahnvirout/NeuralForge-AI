import re


def detect_risky_hyperparameters(code, file_path):
    """
    Flags common risky hyperparameter choices in tree-based models —
    e.g. no max_depth set, which allows unlimited tree growth and overfitting.
    """
    issues = []

    tree_models = ["DecisionTreeClassifier", "DecisionTreeRegressor",
                   "RandomForestClassifier", "RandomForestRegressor"]

    for model_name in tree_models:
        if model_name in code:
            # crude check: does the model call include max_depth anywhere nearby?
            pattern = rf"{model_name}\s*\([^)]*\)"
            match = re.search(pattern, code)

            if match:
                call_text = match.group()
                if "max_depth" not in call_text:
                    issues.append({
                        "file": file_path,
                        "issue": f"{model_name} initialized without max_depth — tree can grow unbounded, risking overfitting",
                        "severity": "medium",
                        "suggestion": "Set max_depth (or min_samples_leaf) to constrain tree growth.",
                    })

    return issues


def scan_repository_for_hyperparameter_risk(files):
    all_issues = []
    for file in files:
        issues = detect_risky_hyperparameters(file["code"], file["relative_path"])
        all_issues.extend(issues)
    return all_issues


if __name__ == "__main__":
    risky_code = """
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(criterion="gini")
model.fit(X_train, y_train)
"""

    safe_code = """
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(max_depth=5)
model.fit(X_train, y_train)
"""

    print("--- Risky code (should flag) ---")
    for issue in detect_risky_hyperparameters(risky_code, "risky.py"):
        print(issue)

    print("\n--- Safe code (should show no issues) ---")
    safe_issues = detect_risky_hyperparameters(safe_code, "safe.py")
    print(f"Issues found: {len(safe_issues)}")