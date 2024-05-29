from datetime import datetime
import os
from pathlib import Path


from entoli.base.io import Io

# File system operation


def file_exists(path: Path) -> Io[bool]:
    return Io(lambda: path.exists())


def dir_exists(path: Path) -> Io[bool]:
    return Io(lambda: path.is_dir())


def list_dir(path: Path) -> Io[list[Path]]:
    return Io(lambda: list(path.iterdir()))


def read_file(path: Path) -> Io[str]:
    return Io(lambda: path.read_text())


def write_file(path: Path, content: str) -> Io[None]:
    def _inner() -> None:
        path.write_text(content)

    return Io(_inner)


def append_file(path: Path, content: str) -> Io[None]:
    def _inner() -> None:
        path.write_text(path.read_text() + content)

    return Io(_inner)


def create_dir(path: Path) -> Io[None]:
    return Io(lambda: path.mkdir())


def create_dir_if_missing(parent_as_well: bool, path: Path) -> Io[None]:
    return Io(lambda: path.mkdir(parents=parent_as_well, exist_ok=True))


def remove_file(path: Path) -> Io[None]:
    return Io(lambda: path.unlink())


def remove_dir(path: Path) -> Io[None]:
    return Io(lambda: path.rmdir())


def remove_dir_rec(path: Path) -> Io[None]:
    return Io(lambda: path.rmdir())


# todo


def get_permissions(path: Path) -> Io[os.stat_result]:
    return Io(lambda: path.stat())


def set_permissions(path: Path, mode: int) -> Io[None]:
    return Io(lambda: path.chmod(mode))


def get_modification_time(path: Path) -> Io[datetime]:
    return Io(lambda: datetime.fromtimestamp(path.stat().st_mtime))
