import ast
import difflib
import re
from typing import Any, Dict, List, Optional

from evaluation.data_leakage_detector import detect_scaling_before_split


def generate_verified_leakage_fix(code: str, file_path: str) -> Optional[Dict[str, Any]]:
    """
    Deterministically generates a unified-diff auto-fix for preprocessor data leakage.
    Steps:
      1. Reorders dataset splitting before feature scaling.
      2. Fits transformer strictly on training split (X_train).
      3. Transforms test set (X_test) without refitting.
      4. Validates patch by in-memory AST parse and detector re-analysis.
      5. Returns fix only if ast.parse succeeds and all leakage findings are resolved.
    NEVER executes repo code.
    """
    initial_issues = detect_scaling_before_split(code, file_path)
    if not initial_issues:
        return None

    lines = code.splitlines()

    # Search for common fit_transform followed by train_test_split pattern
    fit_line_idx = None
    split_line_idx = None
    scaled_var = None
    raw_var = None
    preproc_obj = None

    for i, line in enumerate(lines):
        # Match: X_scaled = scaler.fit_transform(X)
        match_fit = re.search(r"(\w+)\s*=\s*(\w+)\.fit_transform\((\w+)\)", line)
        if match_fit and fit_line_idx is None:
            fit_line_idx = i
            scaled_var = match_fit.group(1)
            preproc_obj = match_fit.group(2)
            raw_var = match_fit.group(3)

        # Match: X_train, X_test, ... = train_test_split(...)
        if "train_test_split(" in line and split_line_idx is None:
            split_line_idx = i

    if fit_line_idx is None or split_line_idx is None or fit_line_idx >= split_line_idx:
        return None

    # Construct the deterministic patch
    patched_lines = list(lines)

    # 1. Modify train_test_split call line: replace scaled_var with raw_var
    split_line = patched_lines[split_line_idx]
    if scaled_var and raw_var:
        split_line_patched = re.sub(rf"\b{re.escape(scaled_var)}\b", raw_var, split_line)
    else:
        split_line_patched = split_line

    # 2. Extract indentation
    indent = re.match(r"^\s*", lines[fit_line_idx]).group()

    # 3. Create clean post-split transformation lines
    replacement_block = [
        f"{split_line_patched}",
        f"{indent}# Fit transformer strictly on training data",
        f"{indent}{scaled_var}_train = {preproc_obj}.fit_transform(X_train)",
        f"{indent}{scaled_var}_test = {preproc_obj}.transform(X_test)",
    ]

    # Reassemble: Remove original fit line and original split line, place replacement_block at fit position
    patched_lines.pop(split_line_idx)
    patched_lines.pop(fit_line_idx)
    for offset, new_line in enumerate(replacement_block):
        patched_lines.insert(fit_line_idx + offset, new_line)

    # Replace downstream references to X_train with X_train scaled if applicable
    patched_code = "\n".join(patched_lines) + "\n"

    # --- IN-MEMORY RE-ANALYSIS VERIFICATION ---
    # 1. Must parse with AST (no syntax error)
    try:
        ast.parse(patched_code)
    except SyntaxError:
        return None

    # 2. Must re-run detector on patched code and verify 0 leakage findings remain
    recheck_issues = detect_scaling_before_split(patched_code, file_path)
    if len(recheck_issues) > 0:
        return None

    # 3. Generate unified diff
    orig_lines_with_nl = [l + "\n" for l in lines]
    patched_lines_with_nl = [l + "\n" for l in patched_lines]
    diff = list(
        difflib.unified_diff(
            orig_lines_with_nl,
            patched_lines_with_nl,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
    )
    diff_text = "".join(diff)

    return {
        "file": file_path,
        "verified": True,
        "status": "verified by re-analysis",
        "diff": diff_text,
        "patched_code": patched_code,
        "explanation": (
            "Split the dataset prior to feature transformation. "
            f"Fitted {preproc_obj} exclusively on X_train, and applied {preproc_obj}.transform(X_test) "
            "to prevent test set distribution leakage. Validated via in-memory AST re-analysis."
        ),
    }


def generate_all_verified_fixes(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Runs verified auto-fix generator for all Python files in the repository."""
    verified_fixes: List[Dict[str, Any]] = []
    for file_info in files:
        if file_info.get("language") == "Python":
            fix = generate_verified_leakage_fix(file_info["code"], file_info["relative_path"])
            if fix is not None:
                verified_fixes.append(fix)
    return verified_fixes
