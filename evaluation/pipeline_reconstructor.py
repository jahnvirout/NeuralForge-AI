import ast
from typing import Any, Dict, List, Optional


DATA_LOAD_NAMES = {
    "read_csv", "read_table", "read_parquet", "read_sql", "read_excel",
    "read_json", "load_dataset", "load_iris", "load_digits", "load_diabetes",
    "load_boston", "load_wine", "load_breast_cancer", "fetch_openml",
    "fetch_california_housing", "np.load", "genfromtxt", "loadtxt",
}

PREPROCESSING_CALLS = {
    "fit_transform", "StandardScaler", "MinMaxScaler", "RobustScaler",
    "OneHotEncoder", "OrdinalEncoder", "SimpleImputer", "KNNImputer",
    "PCA", "SelectKBest", "TfidfVectorizer", "CountVectorizer",
}

SPLIT_CALLS = {
    "train_test_split", "KFold", "StratifiedKFold", "TimeSeriesSplit",
    "GroupKFold", "ShuffleSplit", "cross_val_score",
}

EVALUATION_CALLS = {
    "score", "evaluate", "predict", "predict_proba", "accuracy_score",
    "precision_score", "recall_score", "f1_score", "roc_auc_score",
    "mean_squared_error", "mean_absolute_error", "r2_score",
    "classification_report", "confusion_matrix",
}


def _get_call_name(node: ast.AST) -> str:
    """Extracts function or method name from Call node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def reconstruct_file_pipeline(code: str, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reconstructs the end-to-end ML pipeline for a single Python file from its AST.
    Traces 5 fundamental stages:
      1. Data Loading
      2. Feature Preprocessing
      3. Dataset Splitting
      4. Model Training (Fit)
      5. Evaluation & Validation
    Returns None if the file has no ML-related operations.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    stages: Dict[str, Dict[str, Any]] = {
        "data_load": {"status": "insufficient evidence", "evidence": "Not found in AST", "line": None},
        "preprocessing": {"status": "insufficient evidence", "evidence": "Not found in AST", "line": None},
        "split": {"status": "insufficient evidence", "evidence": "Not found in AST", "line": None},
        "model_fit": {"status": "insufficient evidence", "evidence": "Not found in AST", "line": None},
        "evaluation": {"status": "insufficient evidence", "evidence": "Not found in AST", "line": None},
    }

    ml_found = False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        call_name = _get_call_name(node.func)

        # 1. Data Loading
        if stages["data_load"]["status"] != "found":
            if call_name in DATA_LOAD_NAMES or "load_" in call_name or "read_" in call_name:
                stages["data_load"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }
                ml_found = True

        # 2. Preprocessing
        if stages["preprocessing"]["status"] != "found":
            if call_name in PREPROCESSING_CALLS or call_name == "fit_transform":
                stages["preprocessing"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }
                ml_found = True

        # 3. Splitting
        if stages["split"]["status"] != "found":
            if call_name in SPLIT_CALLS:
                stages["split"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }
                ml_found = True

        # 4. Model Training (fit)
        if stages["model_fit"]["status"] != "found":
            if call_name == "fit":
                stages["model_fit"] = {
                    "status": "found",
                    "evidence": ".fit()",
                    "line": node.lineno,
                }
                ml_found = True

        # 5. Model Evaluation
        if stages["evaluation"]["status"] != "found":
            if call_name in EVALUATION_CALLS:
                stages["evaluation"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }
                ml_found = True

    if not ml_found:
        return None

    # Generate Graphviz DOT representation
    dot_graph = _generate_dot_graph(stages, file_path)

    return {
        "file": file_path,
        "stages": stages,
        "dot_graph": dot_graph,
        "complete_pipeline": all(s["status"] == "found" for s in stages.values()),
    }


def _generate_dot_graph(stages: Dict[str, Dict[str, Any]], file_path: str) -> str:
    """Generates clean Graphviz DOT syntax for visualizing the reconstructed ML pipeline."""
    labels = {
        "data_load": "1. Data Ingestion",
        "preprocessing": "2. Preprocessing",
        "split": "3. Train/Test Split",
        "model_fit": "4. Model Training",
        "evaluation": "5. Evaluation",
    }

    dot_lines = [
        "digraph MLPipeline {",
        '  rankdir=LR;',
        '  bgcolor="transparent";',
        '  node [shape=box, style="rounded,filled", fontname="Inter, sans-serif", fontsize=10, margin="0.2,0.1"];',
        '  edge [color="#666666", arrowsize=0.8];',
    ]

    stage_keys = ["data_load", "preprocessing", "split", "model_fit", "evaluation"]

    for key in stage_keys:
        info = stages[key]
        lbl = labels[key]
        if info["status"] == "found":
            detail = f"{lbl}\\n({info['evidence']} : L{info['line']})"
            dot_lines.append(
                f'  {key} [label="{detail}", fillcolor="#122417", fontcolor="#ffffff", color="#4ade80"];'
            )
        else:
            detail = f"{lbl}\\n(insufficient evidence)"
            dot_lines.append(
                f'  {key} [label="{detail}", fillcolor="#1c1d24", fontcolor="#888a93", color="#3e4150", style="rounded,dashed"];'
            )

    # Add edges between stages
    for i in range(len(stage_keys) - 1):
        dot_lines.append(f"  {stage_keys[i]} -> {stage_keys[i+1]};")

    dot_lines.append("}")
    return "\n".join(dot_lines)


def reconstruct_repository_pipelines(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reconstructs ML pipelines for all Python scripts in the repository."""
    pipelines = []
    for file_info in files:
        if file_info.get("language") == "Python":
            pipe = reconstruct_file_pipeline(file_info["code"], file_info["relative_path"])
            if pipe is not None:
                pipelines.append(pipe)
    return pipelines
