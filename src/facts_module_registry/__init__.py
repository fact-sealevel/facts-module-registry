from pathlib import Path


def get_registry_dir() -> Path:
    return Path(__file__).resolve().parent
