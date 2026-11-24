import json
from pathlib import Path
from parser.github_ingestion import is_valid_github_url, calculate_analyzable_source_bytes
from parser.repository_parser import parse_repository, scan_committed_data_files
from evaluation.pipeline_reconstructor import reconstruct_file_pipeline
from evaluation.verified_autofix import generate_verified_leakage_fix, validate_fix_variables
from evaluation.project_scorer import score_project


def test_github_url_validation():
    assert is_valid_github_url("https://github.com/scikit-learn/scikit-learn") is True
    assert is_valid_github_url("https://github.com/user-name/repo.git") is True
    assert is_valid_github_url("https://malicious.site/repo") is False
    assert is_valid_github_url("invalid_string") is False
    assert is_valid_github_url("") is False


def test_ipynb_cell_extraction(tmp_path):
    repo_dir = tmp_path / "nb_repo"
    repo_dir.mkdir()
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Title\n", "Some documentation\n"]
            },
            {
                "cell_type": "code",
                "source": [
                    "import numpy as np\n",
                    "arr = np.array([1, 2, 3])\n"
                ]
            }
        ]
    }
    nb_file = repo_dir / "analysis.ipynb"
    nb_file.write_text(json.dumps(notebook_content), encoding="utf-8")

    files = parse_repository(str(repo_dir))
    assert len(files) == 1
    assert files[0]["language"] == "Python"
    assert "np.array" in files[0]["code"]


def test_committed_dataset_detection(tmp_path):
    repo_dir = tmp_path / "data_repo"
    repo_dir.mkdir()
    (repo_dir / "clean_script.py").write_text("print('hello')", encoding="utf-8")
    (repo_dir / "dataset.csv").write_bytes(b"a,b,c\n1,2,3\n")
    (repo_dir / "weights.parquet").write_bytes(b"PAR1dummydata")

    data_files = scan_committed_data_files(str(repo_dir))
    assert len(data_files) == 2
    extensions = {df["extension"] for df in data_files}
    assert ".csv" in extensions
    assert ".parquet" in extensions

    parsed_files = parse_repository(str(repo_dir))
    report = score_project(parsed_files, repo_path=str(repo_dir))
    assert "committed_dataset_issues" in report
    assert len(report["committed_dataset_issues"]) == 2


def test_pipeline_reconstruction():
    code = """
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

df = pd.read_csv("data.csv")
X = df.drop("target", axis=1)
y = df["target"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression()
model.fit(X_train_scaled, y_train)
accuracy = model.score(X_test_scaled, y_test)
"""
    pipeline = reconstruct_file_pipeline(code, "train.py")
    assert pipeline is not None
    assert pipeline["complete_pipeline"] is True
    stages = pipeline["stages"]
    assert stages["data_load"]["status"] == "found"
    assert stages["preprocessing"]["status"] == "found"
    assert stages["split"]["status"] == "found"
    assert stages["model_fit"]["status"] == "found"
    assert stages["evaluation"]["status"] == "found"
    assert "digraph MLPipeline" in pipeline["dot_graph"]


def test_verified_autofix_on_bad_fixture():
    fixture_path = Path("tests/fixtures/bad_model.py")
    assert fixture_path.exists()
    code = fixture_path.read_text(encoding="utf-8")

    fix = generate_verified_leakage_fix(code, "bad_model.py")
    assert fix is not None
    assert fix["verified"] is True
    assert fix["status"].startswith("leakage pattern removed")
    assert "--- a/bad_model.py" in fix["diff"]
    assert "+++ b/bad_model.py" in fix["diff"]
    assert "fit_transform(X_train)" in fix["patched_code"]


def test_autofix_2way_split():
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test = train_test_split(X_scaled, test_size=0.2)
"""
    fix = generate_verified_leakage_fix(code, "test_2way.py")
    assert fix is not None
    assert fix["verified"] is True
    assert "train_test_split(X, test_size=0.2)" in fix["patched_code"]
    assert "X_train = scaler.fit_transform(X_train)" in fix["patched_code"]
    assert "X_test = scaler.transform(X_test)" in fix["patched_code"]
    assert fix["status"] == "leakage pattern removed (re-analysis + ast.parse passed); semantic equivalence not guaranteed"
    assert "semantic equivalence not guaranteed" in fix["explanation"]


def test_autofix_4way_split():
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
"""
    fix = generate_verified_leakage_fix(code, "test_4way.py")
    assert fix is not None
    assert fix["verified"] is True
    assert "train_test_split(X, y, test_size=0.2)" in fix["patched_code"]
    assert "X_train = scaler.fit_transform(X_train)" in fix["patched_code"]
    assert "X_test = scaler.transform(X_test)" in fix["patched_code"]


def test_autofix_downstream_uses_scaled_data():
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

model = LogisticRegression()
model.fit(X_train, y_train)
acc = model.score(X_test, y_test)
"""
    fix = generate_verified_leakage_fix(code, "pipeline.py")
    assert fix is not None
    assert fix["verified"] is True
    assert "X_train = scaler.fit_transform(X_train)" in fix["patched_code"]
    assert "X_test = scaler.transform(X_test)" in fix["patched_code"]
    assert "model.fit(X_train, y_train)" in fix["patched_code"]
    assert "model.score(X_test, y_test)" in fix["patched_code"]
    assert "X_scaled" not in fix["patched_code"]


def test_autofix_unused_new_variable_rejection():
    code = """
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test = train_test_split(X_scaled, y, test_size=0.2)

model = LogisticRegression()
model.fit(X_train, y_train)
"""
    patched_unused = code.replace("X_scaled = scaler.fit_transform(X)", "") + "\nX_new = scaler.fit_transform(X_train)\n"
    assert validate_fix_variables(patched_unused, assigned_by_fix={"X_new"}, split_vars={"X_train", "X_test"}, fix_end_line=7) is False

    fix = generate_verified_leakage_fix(code, "test.py", _assign_new_vars=True)
    assert fix is None


def test_large_repo_analyze_truncated_and_upload_413(tmp_path, monkeypatch):
    import config
    import backend.main
    from fastapi.testclient import TestClient
    from backend.main import app

    repo_dir = tmp_path / "large_repo"
    repo_dir.mkdir()
    (repo_dir / "a.py").write_text("x = 1\n", encoding="utf-8")
    (repo_dir / "b.py").write_text("y = 2\n" * 50, encoding="utf-8")
    (repo_dir / "c.py").write_text("z = 3\n" * 100, encoding="utf-8")

    monkeypatch.setattr(config, "MAX_ANALYZABLE_SOURCE_BYTES", 50)
    monkeypatch.setattr(backend.main, "MAX_ANALYZABLE_SOURCE_BYTES", 50)

    client = TestClient(app)

    # /analyze returns 200 with truncated=True, not 413
    res_analyze = client.post("/analyze", json={"repo_path": str(repo_dir)})
    assert res_analyze.status_code == 200
    data_analyze = res_analyze.json()
    assert data_analyze["truncated"] is True
    assert data_analyze["files_scanned"] >= 1
    assert data_analyze["files_skipped"] >= 1
    assert data_analyze["total_files"] == 3

    # /upload-repo still returns 413
    res_upload = client.post("/upload-repo", json={"repo_path": str(repo_dir)})
    assert res_upload.status_code == 413
    assert "exceeds" in res_upload.json()["detail"].lower()


def test_pipeline_load_balancing_loss_not_data_ingestion():
    from evaluation.pipeline_reconstructor import _is_data_ingestion_call, reconstruct_file_pipeline
    assert _is_data_ingestion_call("", "load_balancing_loss_func") is False
    assert _is_data_ingestion_call("model", "load_state_dict") is False
    assert _is_data_ingestion_call("path", "read_text") is False

    code = """
loss = load_balancing_loss_func(x)
state = model.load_state_dict(weights)
txt = path.read_text()
"""
    pipe = reconstruct_file_pipeline(code, "loss_util.py")
    assert pipe is None


def test_pipeline_single_stage_returns_no_pipeline():
    from evaluation.pipeline_reconstructor import reconstruct_file_pipeline
    code_ingest_only = """
import pandas as pd
df = pd.read_csv("data.csv")
print(df.shape)
"""
    assert reconstruct_file_pipeline(code_ingest_only, "ingest.py") is None

    code_fit_only = """
model.fit(X, y)
"""
    assert reconstruct_file_pipeline(code_fit_only, "train_only.py") is None


def test_analyze_on_repo_with_20_non_training_files_returns_zero_pipelines(tmp_path):
    from fastapi.testclient import TestClient
    from backend.main import app

    repo_dir = tmp_path / "non_training_repo"
    repo_dir.mkdir()
    for i in range(20):
        (repo_dir / f"module_{i}.py").write_text(f"""
def process_data_{i}(val):
    return val * {i}
""", encoding="utf-8")

    client = TestClient(app)
    res = client.post("/analyze", json={"repo_path": str(repo_dir)})
    assert res.status_code == 200
    data = res.json()
    assert len(data.get("pipelines", [])) == 0
    assert "timing" in data
    assert "clone_s" in data["timing"]
    assert "scan_s" in data["timing"]
    assert "pipeline_s" in data["timing"]


