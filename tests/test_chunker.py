from chunking.python_chunker import chunk_python_file


def test_chunker_finds_functions():
    sample_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
    result = chunk_python_file(sample_code, "sample.py")
    assert len(result) == 2


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


def test_chunker_handles_syntax_error():
    bad_code = "def broken(:\n  pass"
    result = chunk_python_file(bad_code, "broken.py")
    assert result == []