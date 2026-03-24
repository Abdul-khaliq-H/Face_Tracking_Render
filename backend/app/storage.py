from pathlib import Path
from uuid import uuid4

from app.config import settings


def ensure_storage_dirs() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.processed_dir).mkdir(parents=True, exist_ok=True)


def make_upload_path(filename: str) -> Path:
    suffix = Path(filename).suffix or ".mp4"
    return Path(settings.upload_dir) / f"{uuid4().hex}{suffix}"


def make_output_path(filename: str) -> Path:
    suffix = Path(filename).suffix or ".mp4"
    return Path(settings.processed_dir) / f"{uuid4().hex}{suffix}"

