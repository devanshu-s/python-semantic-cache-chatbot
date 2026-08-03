import os
from datetime import datetime, timezone

def get_current_timestamp() -> str:
    """Return formatted ISO timestamp string in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def ensure_directory_exists(filepath: str) -> None:
    """Ensure parent directory of a given file path exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
