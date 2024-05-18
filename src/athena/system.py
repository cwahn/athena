from pathlib import Path

from athena.base.io import Io


def file_exists(path: Path) -> Io[bool]:
    return Io(lambda: path.exists())


def dir_exists(path: Path) -> Io[bool]:
    return Io(lambda: path.is_dir())


def read_file(path: Path) -> Io[str]:
    return Io(lambda: path.read_text())


def list_dir(path: Path) -> Io[list[Path]]:
    return Io(lambda: list(path.iterdir()))


def write_file(path: Path, content: str) -> Io[None]:
    def _inner() -> None:
        path.write_text(content)

    return Io(_inner)


def append_file(path: Path, content: str) -> Io[None]:
    def _inner() -> None:
        path.write_text(path.read_text() + content)

    return Io(_inner)


def remove_file(path: Path) -> Io[None]:
    return Io(lambda: path.unlink())


def remove_dir(path: Path) -> Io[None]:
    return Io(lambda: path.rmdir())


def remove_dir_rec(path: Path) -> Io[None]:
    return Io(lambda: path.rmdir())
