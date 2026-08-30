from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "cobol" / "src").is_dir() and (parent / "cobol" / "copybooks").is_dir():
            return parent
    raise FileNotFoundError("Could not locate repository root (cobol/src missing).")


def cobol_src() -> Path:
    return repo_root() / "cobol" / "src"


def copybook_dir() -> Path:
    return repo_root() / "cobol" / "copybooks"


def data_dir() -> Path:
    return repo_root() / "cobol" / "data"


def bin_dir() -> Path:
    return repo_root() / "bin"


def work_dir() -> Path:
    return repo_root() / "work"
