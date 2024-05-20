from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import subprocess
from typing import IO, Any, Dict, List, Tuple, Union


from entoli.base.maybe import Just, Maybe, Nothing

from .base.io import Io

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


# def proc(command: str) -> Io[subprocess.Popen]:
#     def _inner() -> subprocess.Popen:
#         return subprocess.Popen(
#             command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
#         )

#     return Io(_inner)


# def shell(command: str) -> Io[None]:
#     def _inner() -> None:
#         result = subprocess.run(command, shell=True)
#         if result.returncode != 0:
#             raise subprocess.CalledProcessError(result.returncode, command)

#     return Io(_inner)


def terminate_process(process: subprocess.Popen) -> Io[None]:
    return Io(lambda: process.terminate())


def get_process_exit_code(process: subprocess.Popen) -> Io[Maybe[int]]:
    def _inner() -> Maybe[int]:
        if code := process.poll() is None:
            return Nothing()
        else:
            return Just(code)

    return Io(_inner)


# Shell interaction functions

# s


@dataclass
class CreateProcess:
    command: str
    use_shell: bool = True
    cwd: Maybe[str] = Nothing()
    env: Maybe[Dict[str, str]] = Nothing()
    std_in: Maybe[Any] = field(default_factory=lambda: Just(subprocess.PIPE))
    std_out: Maybe[Any] = field(default_factory=lambda: Just(subprocess.PIPE))
    std_err: Maybe[Any] = field(default_factory=lambda: Just(subprocess.PIPE))


# shell function
def shell(command: str) -> CreateProcess:
    return CreateProcess(command=command, use_shell=True)


# proc function
def proc(path: str, args: List[str]) -> CreateProcess:
    return CreateProcess(command=f"{path} {' '.join(args)}", use_shell=False)


# create_process function
# def create_process(
#     proc: CreateProcess,
# ) -> Io[Tuple[Maybe, Maybe, Maybe, subprocess.Popen]]:
#     def _inner() -> Tuple[Maybe, Maybe, Maybe, subprocess.Popen]:
#         process = subprocess.Popen(
#             proc.command,
#             shell=proc.use_shell,
#             cwd=proc.cwd,
#             env=proc.env,
#             stdin=proc.std_in,
#             stdout=proc.std_out,
#             stderr=proc.std_err,
#             text=True,  # Ensures text mode (string IO)
#         )
#         stdin = Just(process.stdin) if process.stdin else Nothing()
#         stdout = Just(process.stdout) if process.stdout else Nothing()
#         stderr = Just(process.stderr) if process.stderr else Nothing()
#         return (stdin, stdout, stderr, process)

#     return Io(_inner)


def create_process(
    proc: CreateProcess,
) -> Io[Tuple[Maybe[IO[str]], Maybe[IO[str]], Maybe[IO[str]], subprocess.Popen]]:
    def _inner() -> (
        Tuple[Maybe[IO[str]], Maybe[IO[str]], Maybe[IO[str]], subprocess.Popen]
    ):
        process = subprocess.Popen(
            proc.command,
            shell=proc.use_shell,
            cwd=proc.cwd.unwrap_or(None),  # type: ignore
            env=proc.env.unwrap_or(None),  # type: ignore
            stdin=proc.std_in.unwrap_or(subprocess.PIPE),
            stdout=proc.std_out.unwrap_or(subprocess.PIPE),
            stderr=proc.std_err.unwrap_or(subprocess.PIPE),
            text=True,  # Ensures text mode (string IO)
        )
        stdin = Just(process.stdin) if process.stdin else Nothing()
        stdout = Just(process.stdout) if process.stdout else Nothing()
        stderr = Just(process.stderr) if process.stderr else Nothing()
        return (stdin, stdout, stderr, process)

    return Io(_inner)


def h_put_str_ln(handle: IO[str], string: str) -> Io[None]:
    def _inner():
        handle.write(string + "\n")
        handle.flush()

    return Io(_inner)


def h_get_line(handle: IO[str]) -> Io[str]:
    def _inner() -> str:
        return handle.readline().strip()

    return Io(_inner)


def h_get_contents(handle: IO[str]) -> Io[str]:
    def _inner():
        return handle.read()

    return Io(_inner)


def wait_for_process(process: subprocess.Popen) -> Io[int]:
    def _inner() -> int:
        return process.wait()

    return Io(_inner)
