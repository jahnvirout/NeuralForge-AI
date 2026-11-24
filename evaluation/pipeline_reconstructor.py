import ast
from typing import Any, Dict, List, Optional, Tuple


PANDAS_LOADERS = {
    "read_csv", "read_table", "read_parquet", "read_sql", "read_sql_query",
    "read_sql_table", "read_excel", "read_json", "read_feather", "read_hdf",
    "read_stata", "read_sas", "read_pickle",
}

NUMPY_LOADERS = {
    "load", "loadtxt", "genfromtxt", "fromfile", "fromregex",
}

DATASET_LOADERS = {
    "load_dataset",
    "load_iris", "load_digits", "load_diabetes", "load_wine", "load_breast_cancer",
    "load_linnerud", "fetch_openml", "fetch_california_housing", "fetch_20newsgroups",
    "fetch_lfw_people", "fetch_olivetti_faces", "fetch_rcv1", "fetch_kddcup99",
    "fetch_covtype", "make_classification", "make_regression", "make_blobs",
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


def _get_call_details(node: ast.AST) -> Tuple[str, str]:
    """Extracts (prefix, func_name) from Call node, e.g. ('pd', 'read_csv') or ('', 'load_dataset')."""
    if isinstance(node, ast.Name):
        return ("", node.id)
    if isinstance(node, ast.Attribute):
        value_name = ""
        if isinstance(node.value, ast.Name):
            value_name = node.value.id
        elif isinstance(node.value, ast.Attribute):
            value_name = node.value.attr
        return (value_name, node.attr)
    return ("", "")


def _is_data_ingestion_call(prefix: str, func_name: str) -> bool:
    """Matches only real data loader calls, never arbitrary load_ or read_ prefixes."""
    if func_name in PANDAS_LOADERS:
        return prefix in ("pd", "pandas", "")
    if func_name in NUMPY_LOADERS:
        if func_name == "load":
            return prefix in ("np", "numpy")
        return prefix in ("np", "numpy", "")
    if func_name in DATASET_LOADERS:
        return True
    return False


def is_training_script(code: str) -> bool:
    """Checks whether a Python script contains evidence of model training (split call AND fit call)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    has_split = False
    has_fit = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            prefix, func_name = _get_call_details(node.func)
            if func_name in SPLIT_CALLS:
                has_split = True
            elif func_name == "fit":
                has_fit = True

            if has_split and has_fit:
                return True

    return False


def reconstruct_file_pipeline(code: str, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Reconstructs the end-to-end ML pipeline for a single Python file from its AST.
    Traces 5 fundamental stages:
      1. Data Loading (matched by real loaders, never prefix)
      2. Feature Preprocessing
      3. Dataset Splitting
      4. Model Training (fit)
      5. Evaluation (score/predict only if fit is present)
    Returns None if fewer than 2 stages have evidence.
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

    has_fit = False
    eval_candidate = None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        prefix, call_name = _get_call_details(node.func)

        # 1. Data Loading (strict exact calls, no prefix matching)
        if stages["data_load"]["status"] != "found":
            if _is_data_ingestion_call(prefix, call_name):
                call_display = f"{prefix}.{call_name}()" if prefix else f"{call_name}()"
                stages["data_load"] = {
                    "status": "found",
                    "evidence": call_display,
                    "line": node.lineno,
                }

        # 2. Preprocessing
        if stages["preprocessing"]["status"] != "found":
            if call_name in PREPROCESSING_CALLS or call_name == "fit_transform":
                stages["preprocessing"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }

        # 3. Splitting
        if stages["split"]["status"] != "found":
            if call_name in SPLIT_CALLS:
                stages["split"] = {
                    "status": "found",
                    "evidence": f"{call_name}()",
                    "line": node.lineno,
                }

        # 4. Model Training (fit)
        if call_name == "fit":
            has_fit = True
            if stages["model_fit"]["status"] != "found":
                stages["model_fit"] = {
                    "status": "found",
                    "evidence": ".fit()",
                    "line": node.lineno,
                }

        # 5. Model Evaluation (candidate tracked, accepted only if has_fit)
        if call_name in EVALUATION_CALLS and eval_candidate is None:
            eval_candidate = {
                "evidence": f"{call_name}()",
                "line": node.lineno,
            }

    # Evaluation only counts when the same file also has a fit call
    if has_fit and eval_candidate is not None:
        stages["evaluation"] = {
            "status": "found",
            "evidence": eval_candidate["evidence"],
            "line": eval_candidate["line"],
        }

    # Reject files with fewer than 2 stages with evidence
    stages_with_evidence = sum(1 for s in stages.values() if s["status"] == "found")
    if stages_with_evidence < 2:
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
