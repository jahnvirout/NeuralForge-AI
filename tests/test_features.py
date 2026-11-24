import json
from pathlib import Path
from parser.github_ingestion import is_valid_github_url, calculate_analyzable_source_bytes
from parser.repository_parser import parse_repository, scan_committed_data_files
from evaluation.pipeline_reconstructor import reconstruct_file_pipeline
from evaluation.verified_autofix import generate_verified_leakage_fix
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
    assert fix["status"] == "verified by re-analysis"
    assert "--- a/bad_model.py" in fix["diff"]
    assert "+++ b/bad_model.py" in fix["diff"]
    assert "fit_transform(X_train)" in fix["patched_code"]
