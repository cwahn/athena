from pathlib import Path
import subprocess
from entoli.base.io import Io
from entoli.base.maybe import Just, Maybe, Nothing
from typing import IO, List, Tuple, Dict, Any
from dataclasses import dataclass, field


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


# Shell interaction functions


@dataclass
class CreateProcess:
    command: str
    use_shell: bool = True
    cwd: Maybe[Path] = field(default_factory=lambda: Nothing())
    env: Maybe[Dict[str, str]] = field(default_factory=lambda: Nothing())
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
            stdin=proc.std_in.unwrap_or(None),
            stdout=proc.std_out.unwrap_or(None),
            stderr=proc.std_err.unwrap_or(None),
            text=True,  # Ensures binary mode (bytes IO)
        )

        mb_stdin = Just(process.stdin) if process.stdin else Nothing()
        mb_stdout = Just(process.stdout) if process.stdout else Nothing()
        mb_stderr = Just(process.stderr) if process.stderr else Nothing()

        return (mb_stdin, mb_stdout, mb_stderr, process)

    return Io(_inner)


def h_put_str_ln(handle: IO[str], string: str) -> Io[None]:
    def _h_put_str_ln():
        handle.write(string + "\n")
        handle.flush()

    return Io(_h_put_str_ln)


def h_get_line(handle: IO[str]) -> Io[str]:
    def _h_get_line() -> str:
        return handle.readline().strip()

    return Io(_h_get_line)


def h_get_contents(handle: IO[str]) -> Io[str]:
    def _h_get_contents() -> str:
        return handle.read()

    return Io(_h_get_contents)


def terminate_process(process: subprocess.Popen) -> Io[None]:
    return Io(lambda: process.terminate())


def wait_for_process(process: subprocess.Popen) -> Io[int]:
    def _wait_for_process() -> int:
        return process.wait()

    return Io(_wait_for_process)


def get_process_exit_code(process: subprocess.Popen) -> Io[Maybe[int]]:
    def _inner() -> Maybe[int]:
        if code := process.poll() is None:
            return Nothing()
        else:
            return Just(code)

    return Io(_inner)
