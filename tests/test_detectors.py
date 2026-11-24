from pathlib import Path
from evaluation.data_leakage_detector import detect_scaling_before_split, scan_repository_for_leakage
from evaluation.overfitting_analyzer import detect_no_validation, scan_repository_for_overfitting_risk
from evaluation.hyperparameter_analyzer import detect_risky_hyperparameters, scan_repository_for_hyperparameter_risk
from evaluation.project_scorer import score_project
from parser.repository_parser import parse_repository


# -------------------------------------------------------------------------
# Data Leakage Detector Tests
# -------------------------------------------------------------------------

def test_leakage_true_positive():
    """True positive: Preprocessor fitted on whole dataset before split."""
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
"""
    issues = detect_scaling_before_split(code, "leak_test.py")
    assert len(issues) == 1
    assert issues[0]["severity"] == "high"
    assert issues[0]["confidence"] == "high"
    assert "fit_transform" in issues[0]["issue"] or "data leakage" in issues[0]["issue"].lower()
    assert issues[0]["line"] == 6


def test_leakage_true_negative_split_first():
    """True negative: Data split first, fit_transform called strictly on training data."""
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
"""
    issues = detect_scaling_before_split(code, "clean_test.py")
    assert len(issues) == 0


def test_leakage_false_positive_strings_and_comments():
    """String and comment false-positive case: comments/docstrings must never trigger leakage."""
    code = '''
# Example: fit_transform(X) should never be called before train_test_split(X, y)
"""
Docstring mentioning fit_transform(data) and train_test_split(data) for educational purposes.
"""
def my_func():
    msg = "fit_transform(X) followed by train_test_split(X)"
    return msg
'''
    issues = detect_scaling_before_split(code, "strings_comments.py")
    assert len(issues) == 0


def test_leakage_cross_function_scope():
    """Scope awareness: fit_transform in one function and train_test_split in another do not leak."""
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def prepare_submission(X_eval):
    # Fits on eval dataset for an external benchmark
    scaler = StandardScaler()
    return scaler.fit_transform(X_eval)

def train_pipeline(X_raw, y_raw):
    # Completely independent split
    X_train, X_test, y_train, y_test = train_test_split(X_raw, y_raw, test_size=0.2)
    return X_train, X_test
"""
    issues = detect_scaling_before_split(code, "cross_func.py")
    assert len(issues) == 0


# -------------------------------------------------------------------------
# Overfitting Analyzer Tests
# -------------------------------------------------------------------------

def test_overfitting_true_positive():
    """True positive: Estimator fit called without any evaluation or score."""
    code = """
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
model.fit(X_train, y_train)
# No score or evaluation call follows
"""
    issues = detect_no_validation(code, "overfit_test.py")
    assert len(issues) == 1
    assert issues[0]["severity"] == "medium"
    assert "never evaluated" in issues[0]["issue"]


def test_overfitting_true_negative():
    """True negative: Estimator fit followed by score on test data."""
    code = """
from sklearn.linear_model import LogisticRegression

model = LogisticRegression()
model.fit(X_train, y_train)
acc = model.score(X_test, y_test)
"""
    issues = detect_no_validation(code, "safe_test.py")
    assert len(issues) == 0


def test_overfitting_comments_and_strings():
    """Comments and docstrings mentioning .fit() must not trigger overfitting alert."""
    code = '''
# Notes: Always remember to call model.fit(X, y) in your training loop.
"""
This module discusses how .fit(X, y) operates internally.
"""
def utility_function():
    return "model.fit(X, y)"
'''
    issues = detect_no_validation(code, "comments.py")
    assert len(issues) == 0


# -------------------------------------------------------------------------
# Hyperparameter Analyzer Tests
# -------------------------------------------------------------------------

def test_hyperparameter_true_positive():
    """True positive: Tree model instantiated without depth or leaf boundary."""
    code = """
from sklearn.tree import DecisionTreeClassifier

clf = DecisionTreeClassifier(criterion="gini")
"""
    issues = detect_risky_hyperparameters(code, "tree_test.py")
    assert len(issues) == 1
    assert "max_depth" in issues[0]["issue"]
    assert issues[0]["severity"] == "medium"


def test_hyperparameter_true_negative():
    """True negative: Tree model with max_depth defined."""
    code = """
from sklearn.tree import DecisionTreeClassifier

clf = DecisionTreeClassifier(max_depth=5, criterion="gini")
"""
    issues = detect_risky_hyperparameters(code, "safe_tree.py")
    assert len(issues) == 0


def test_hyperparameter_import_only_not_flagged():
    """Import statements or string mentions of DecisionTreeClassifier must not trigger."""
    code = """
from sklearn.tree import DecisionTreeClassifier
# Just importing DecisionTreeClassifier without instantiation
help_text = "Use DecisionTreeClassifier(max_depth=4)"
"""
    issues = detect_risky_hyperparameters(code, "import_test.py")
    assert len(issues) == 0


# -------------------------------------------------------------------------
# Self-Scan & Regression Tests
# -------------------------------------------------------------------------

def test_evaluation_folder_self_scan_zero_findings():
    """
    Regression test: Scanning this repo's evaluation/ folder MUST produce 0 findings.
    AST analysis guarantees strings/docstrings/comments inside detector code never self-flag.
    """
    eval_files = parse_repository("evaluation")
    assert len(eval_files) >= 4, "Expected at least 4 files in evaluation/"

    report = score_project(eval_files)
    assert report["total_issues"] == 0, f"Expected 0 issues in evaluation/, found {report['total_issues']}: {report}"
    assert report["overall_score"] == 100


def test_explainable_score_breakdown():
    """Verifies that project_scorer returns a clear rule-by-rule points breakdown."""
    code_bad = """
from sklearn.tree import DecisionTreeClassifier
clf = DecisionTreeClassifier()
"""
    files = [{"relative_path": "test.py", "language": "Python", "code": code_bad}]
    report = score_project(files)
    assert "score_breakdown" in report
    breakdown = report["score_breakdown"]
    assert len(breakdown) == 3
    # Check that rule names and point deductions are explicitly populated
    hyper_item = next(item for item in breakdown if item["category"] == "hyperparameter_risk")
    assert hyper_item["issues_count"] == 1
    assert hyper_item["points_deducted"] == 5


def test_fixture_bad_model_detected():
    """Verifies that deliberate test fixture tests/fixtures/bad_model.py flags leakage and overfitting."""
    fixture_path = Path("tests/fixtures/bad_model.py")
    assert fixture_path.exists()
    code = fixture_path.read_text(encoding="utf-8")

    leakage = detect_scaling_before_split(code, "bad_model.py")
    assert len(leakage) == 1
    assert leakage[0]["severity"] == "high"

    overfitting = detect_no_validation(code, "bad_model.py")
    assert len(overfitting) == 1
    assert overfitting[0]["severity"] == "medium"


def test_neuralforgeignore_respected(tmp_path):
    """Verifies that .neuralforgeignore correctly excludes specified files and directories."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "valid.py").write_text("x = 1\n", encoding="utf-8")
    (repo_dir / "ignored.py").write_text("y = 2\n", encoding="utf-8")
    (repo_dir / ".neuralforgeignore").write_text("ignored.py\n", encoding="utf-8")

    parsed = parse_repository(str(repo_dir))
    names = [f["file_name"] for f in parsed]
    assert "valid.py" in names
    assert "ignored.py" not in names

