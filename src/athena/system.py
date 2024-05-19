from pathlib import Path
import subprocess
from typing import List, Tuple, Union

from base.io import Io

# File system operation


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


# todo

# getPermissions
# setPermissions
# getModificationTime


# Shell operations


# Shell operation to run a command and capture its output


def call_command(command: str) -> Io[None]:
    def _inner() -> None:
        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, command)

    return Io(_inner)


def call_process(program: str, args: List[str]) -> Io[None]:
    def _inner() -> None:
        result = subprocess.run([program] + args)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, [program] + args)

    return Io(_inner)


def read_process(program: str, args: List[str], input: str = "") -> Io[str]:
    def _inner() -> str:
        result = subprocess.run(
            [program] + args,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, [program] + args, result.stdout, result.stderr
            )
        return result.stdout

    return Io(_inner)


def read_process_with_exit_code(
    program: str, args: List[str], input: str = ""
) -> Io[Tuple[int, str, str]]:
    def _inner() -> Tuple[int, str, str]:
        result = subprocess.run(
            [program] + args,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return (result.returncode, result.stdout, result.stderr)

    return Io(_inner)


# todo

# createProcess
# proc
# shell
# waitForProcess
# terminateProcess
# getProcessExitCode

# Example usage
if __name__ == "__main__":
    # Running a process and capturing output
    try:
        output = read_process("echo", ["Hello, Haskell!"]).action()
        print(f"Process Output: {output}")
    except subprocess.CalledProcessError as e:
        print(f"Process failed with error: {e}")

    # Running a process and capturing output and exit code
    try:
        exit_code, stdout, stderr = read_process_with_exit_code(
            "ls", ["non_existing_directory"]
        ).action()
        print(f"Exit Code: {exit_code}")
        print(f"Standard Output: {stdout}")
        print(f"Standard Error: {stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Process failed with error: {e}")
