# NeuralForge AI | Day 3 | Testing with pytest

## Why do we need tests?

So far, we built two modules:

```text
Repository Parser  -> collects source-code files
Python Chunker     -> splits Python code into functions/classes
```

Both modules may work today. But later, when we change the code, we can accidentally break something that was already working.

Example: imagine we add support for another language and accidentally remove Python from `SUPPORTED_EXTENSIONS`. The parser may still run without an error, but it will stop finding Python files.

This is why we write tests.

A test is a small program that checks one expected behaviour automatically.

```text
Input
  -> run our function
  -> compare actual output with expected output
  -> pass or fail
```

Tests are like a safety net. They do not build the feature; they prove that the feature behaves the way we promised.

---

## What is pytest?

`pytest` is a Python testing framework. It automatically finds test files and runs test functions.

By convention:

```text
tests/test_parser.py       -> test file
def test_parser_finds_all_files():  -> test function
```

The `test_` prefix is important. pytest uses it to discover what it should run.

To run all tests from the project root:

```bash
pytest -q
```

`-q` means quiet mode: pytest prints a compact summary instead of lots of detail.

---

# File 1: `tests/test_parser.py`

## Goal

This file tests the Repository Parser. It checks that the parser:

- finds the expected source-code files;
- gives them the correct language label;
- skips folders that should be ignored.

The code being tested lives in:

```text
parser/repository_parser.py
```

The test data lives in:

```text
data/sample_repo/
```

That sample repository contains three Python files:

```text
calculator.py
search.py
sorting.py
```

## Import (line 1)

```python
from parser.repository_parser import parse_repository
```

This imports the real `parse_repository()` function from our parser module.

Important: the test does not rewrite the parsing logic. It calls the actual production function exactly the same way the rest of NeuralForge would call it.

Think of it like testing a calculator. We do not build a second calculator inside the test; we press buttons on the real calculator and check whether it gives the right answer.

---

## Test 1: Finding all files (lines 4-6)

```python
def test_parser_finds_all_files():
    result = parse_repository("data/sample_repo")
    assert len(result) == 3
```

### `def test_parser_finds_all_files():`

This creates one test case. Its name clearly describes the behaviour we expect: the parser should find all valid files.

### `result = parse_repository("data/sample_repo")`

We give the parser the path to our small sample repository. It returns a list of file dictionaries.

Conceptually, `result` should look like this:

```python
[
    {"file_name": "calculator.py", "language": "Python", ...},
    {"file_name": "search.py", "language": "Python", ...},
    {"file_name": "sorting.py", "language": "Python", ...}
]
```

### `assert len(result) == 3`

`len(result)` counts how many items are in the list.

`assert` means: “this condition must be true.”

- If the parser returns 3 files, `3 == 3` is true and the test passes.
- If it returns 2 or 4 files, the condition is false and pytest fails the test.

Why this matters: it protects us from regressions where the parser accidentally skips a valid file or starts including an unwanted file.

---

## Test 2: Correct language metadata (lines 9-12)

```python
def test_parser_returns_correct_language():
    result = parse_repository("data/sample_repo")
    for file in result:
        assert file["language"] == "Python"
```

The parser does not only return the code. It also stores metadata, including the language.

### `for file in result:`

This loop checks every parsed file one by one.

`file` here is a dictionary such as:

```python
{
    "file_name": "calculator.py",
    "relative_path": "calculator.py",
    "language": "Python",
    "code": "..."
}
```

### `assert file["language"] == "Python"`

All files in `data/sample_repo` have the `.py` extension. The parser's `SUPPORTED_EXTENSIONS` dictionary maps `.py` to `Python`, so every returned dictionary must contain:

```python
"language": "Python"
```

Why this matters: later modules may use language metadata to decide which chunker or processing pipeline to use. Wrong metadata means a correct file could be sent to the wrong handler.

---

## Test 3: Ignored directories (lines 15-19)

```python
def test_parser_skips_ignored_dirs():
    result = parse_repository("data/sample_repo")
    for file in result:
        assert "venv" not in file["relative_path"]
        assert "__pycache__" not in file["relative_path"]
```

Real repositories often contain folders that are not part of the developer's actual source code:

- `venv` contains installed Python packages;
- `__pycache__` contains automatically generated Python bytecode;
- `.git` contains Git internals;
- `node_modules` contains installed JavaScript packages.

We do not want NeuralForge to read and embed these folders. They are noisy, can be huge, and make retrieval worse.

### `assert "venv" not in file["relative_path"]`

This verifies that none of the returned file paths came from a virtual environment.

### `assert "__pycache__" not in file["relative_path"]`

This verifies that none of the returned file paths came from Python's cache folder.

The parser implements this behaviour using:

```python
IGNORED_DIRS = {".git", "node_modules", "venv", "__pycache__", ".pytest_cache"}
```

and then skips a path if one of its folder names belongs to that set.

---

# File 2: `tests/test_chunker.py`

## Goal

This file tests the Python Chunker. It checks that the chunker:

- finds multiple functions as separate chunks;
- labels classes and functions correctly;
- handles invalid Python without crashing.

The real code being tested is:

```text
chunking/python_chunker.py
```

## Import (line 1)

```python
from chunking.python_chunker import chunk_python_file
```

This imports the actual chunking function.

It takes:

```python
chunk_python_file(code, file_path)
```

- `code`: the complete Python file as a string;
- `file_path`: the name/path to attach to each returned chunk.

It returns a list of dictionaries. Each dictionary describes one discovered function or class.

---

## Test 1: Functions become chunks (lines 4-13)

```python
def test_chunker_finds_functions():
    sample_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    result = chunk_python_file(sample_code, "sample.py")
    assert len(result) == 2
```

### `sample_code = """ ... """`

Triple quotes create a multi-line string. This lets the test write a tiny fake Python file directly inside the test.

The fake file contains two top-level functions:

```python
def add(a, b):
def subtract(a, b):
```

We use a small controlled input instead of a real large file because tests should be easy to understand and focused on one behaviour.

### `result = chunk_python_file(sample_code, "sample.py")`

The chunker runs `ast.parse()` internally, builds an AST, finds both function definitions, and produces two chunks.

Conceptually the result contains:

```python
[
    {"name": "add", "chunk_type": "function", ...},
    {"name": "subtract", "chunk_type": "function", ...}
]
```

### `assert len(result) == 2`

There are two functions, so we expect exactly two chunks.

Why this matters: if the AST traversal stops working, or the code accidentally only extracts the first function, this test immediately catches it.

---

## Test 2: Identifying chunk types (lines 16-27)

```python
def test_chunker_identifies_type_correctly():
    sample_code = """
class Calculator:
    def multiply(self, a, b):
        return a * b
"""
    result = chunk_python_file(sample_code, "sample.py")
    types = [chunk["chunk_type"] for chunk in result]
    assert "class" in types
    assert "function" in types
```

The input contains:

```python
class Calculator:
```

and a method inside it:

```python
def multiply(self, a, b):
```

### `types = [chunk["chunk_type"] for chunk in result]`

This is a list comprehension. It creates a new list containing only the `chunk_type` field from every chunk.

For this input, it becomes roughly:

```python
["class", "function"]
```

Equivalent longer code:

```python
types = []
for chunk in result:
    types.append(chunk["chunk_type"])
```

### `assert "class" in types`

This confirms that the chunker recognised `Calculator` as a class.

### `assert "function" in types`

This confirms that the chunker recognised `multiply` as a function.

Why does it find a method too? `ast.walk(tree)` visits every level of the syntax tree, including nodes nested inside a class.

One current design detail: the chunker creates a class chunk that includes the method and also a separate function chunk for that method. This creates overlapping chunks. It is okay for this early version, but later we may decide whether methods should be separate chunks, class-only chunks, or both depending on retrieval quality.

---

## Test 3: Invalid syntax should not crash (lines 30-33)

```python
def test_chunker_handles_syntax_error():
    bad_code = "def broken(:\n  pass"
    result = chunk_python_file(bad_code, "broken.py")
    assert result == []
```

### `bad_code = "def broken(:\n  pass"`

This is intentionally invalid Python. A parameter list cannot start with `:`.

### What happens internally?

The chunker tries to parse this string:

```python
tree = ast.parse(code)
```

Python raises a `SyntaxError` because the code is malformed. The chunker catches that error:

```python
except SyntaxError as e:
    print(f"Could not parse {file_path}: {e}")
    return chunks
```

Since `chunks` began as an empty list, the function returns `[]`.

### `assert result == []`

The test verifies the safe behaviour: invalid code gives an empty result instead of crashing the whole NeuralForge indexing pipeline.

This is called graceful error handling. A real repository can contain work-in-progress files, merge-conflict mistakes, or unfinished code. One bad file should not stop every other valid file from being processed.

---

# `__pycache__` inside the tests folder

```text
tests/__pycache__/
```

This is not a test file you wrote. Python automatically creates it to store compiled bytecode (`.pyc` files), which can speed up future imports.

Do not edit it. Usually it should be included in `.gitignore`, so it is not committed to Git.

---

# Complete flow

```text
Developer changes parser/chunker code
        ↓
pytest discovers tests/test_*.py
        ↓
Each test calls the real function
        ↓
assert compares actual behaviour to expected behaviour
        ↓
All assertions true  → tests pass
Any assertion false   → test fails and shows what broke
```

# Important interview questions

## Q1. What is unit testing?

**Answer:**

Unit testing means testing a small, isolated piece of code—usually one function or module—to verify that it produces the expected output for a given input.

In NeuralForge, `test_parser.py` tests the repository parser and `test_chunker.py` tests the Python chunker.

---

## Q2. Why did you use pytest?

**Answer:**

pytest is a popular Python testing framework. It automatically discovers files and functions beginning with `test_`, provides simple `assert` statements, and gives clear failure messages when expected behaviour is broken.

---

## Q3. What does `assert` do?

**Answer:**

`assert` checks whether a condition is true. If it is true, the test continues. If it is false, Python raises an assertion error and pytest marks that test as failed.

Example:

```python
assert len(result) == 3
```

means the parser must return exactly three files.

---

## Q4. Why test the parser separately from the chunker?

**Answer:**

They have different responsibilities. The parser collects source files, while the chunker splits Python code into logical units. Testing them separately makes it easier to identify exactly which module broke when a test fails.

---

## Q5. Why use a small sample repository?

**Answer:**

A small sample repository gives predictable input and output. It makes the test fast, readable, and independent of a large real project whose files may change frequently.

---

## Q6. Why test invalid Python syntax?

**Answer:**

Real repositories can contain incomplete or broken files. The chunker should handle a syntax error safely and continue processing the rest of the repository instead of crashing the entire pipeline.

---

## Q7. What is the difference between a unit test and an integration test?

**Answer:**

A unit test checks one small component in isolation, such as `chunk_python_file()`.

An integration test checks whether multiple components work together, for example: parse a repository, send its Python files to the chunker, and verify that chunks are produced.

Our current tests are mostly unit tests. `test_parser.py` uses real sample files, so it also has a small integration aspect with the filesystem.

---

## Q8. What happens if a test fails?

**Answer:**

pytest reports the failing test, the failed assertion, and the actual value it received. That helps us locate which expected behaviour was broken before we merge or deploy the code.

---

## Q9. Do passing tests prove the entire application is perfect?

**Answer:**

No. Tests only prove the cases we wrote tests for. Passing tests give confidence that known expected behaviour works, but we should gradually add more cases, such as empty repositories, unsupported file types, large files, nested folders, decorators, and async functions.

---

## Q10. What is a regression test?

**Answer:**

A regression test protects behaviour that already worked. If a future change accidentally breaks it, the same test fails and warns us immediately.

---

# One strong interview answer

## Q. Why are tests important in an AI/RAG project?

**Answer:**

An AI/RAG pipeline has multiple stages: parsing, chunking, embeddings, retrieval, and LLM generation. If an early stage silently returns wrong data, every later stage receives bad input and the final answer becomes unreliable. Tests validate each stage's basic contract, so errors are caught close to their source rather than appearing later as confusing bad AI answers.

---

# Small limitations in the current tests

The current tests are a good start, but they do not yet test every edge case.

- The parser test checks that ignored directories are absent, but the current `data/sample_repo` does not appear to contain actual `venv` or `__pycache__` folders. A stronger test would create those folders/files and verify they are skipped.
- The chunker test checks that class and function types exist, but it does not verify exact chunk names, line numbers, or extracted code.
- The chunker currently finds methods as separate function chunks in addition to the enclosing class chunk. Future tests should explicitly document whether that overlap is desired.

This is the right way to explain it in an interview: “I started with core happy-path and error-handling tests, then I would expand coverage around edge cases as the pipeline grows.”
