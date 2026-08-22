from parser.repository_parser import parse_repository


def test_parser_finds_all_files():
    result = parse_repository("data/sample_repo")
    assert len(result) == 4


def test_parser_returns_correct_language():
    result = parse_repository("data/sample_repo")
    for file in result:
        assert file["language"] == "Python"


def test_parser_skips_ignored_dirs():
    result = parse_repository("data/sample_repo")
    for file in result:
        assert "venv" not in file["relative_path"]
        assert "__pycache__" not in file["relative_path"]