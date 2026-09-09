from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
FILES_DIR = PROJECT_ROOT / "files"
RESULTS_DIR = PROJECT_ROOT / "results"


def resolve_from_scripts(path):
    """Resolve legacy relative solver paths against the scripts directory."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return SCRIPTS_DIR / candidate
