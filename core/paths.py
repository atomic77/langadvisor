"""Cross-platform application directories."""

from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "langadvisor"


def data_dir() -> Path:
    """Return the platform-specific user data directory for the app.

    Creates the directory if it does not exist.
    """
    path = Path(user_data_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


HISTORY_DB = data_dir() / "history.db"
