import subprocess
from typing import IO, Tuple, Any, TypeVar, Generic
from pathlib import Path
import os
import io

_A = TypeVar("_A")


# Definition of Maybe, Just, and Nothing
class Maybe:
    pass


class Just(Maybe):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Just({self.value})"


class Nothing(Maybe):
    def __repr__(self):
        return "Nothing"


class Io(Generic[_A]):
    def __init__(self, action):
        self.action = action

    def run(self):
        return self.action()

    def map(self, f):
        return Io(lambda: f(self.run()))

    def flat_map(self, f):
        return Io(lambda: f(self.run()).run())


def create_process(command: str) -> Io[Tuple[Maybe, Maybe, Maybe, subprocess.Popen]]:
    def _inner() -> Tuple[Maybe, Maybe, Maybe, subprocess.Popen]:
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdin = Just(process.stdin) if process.stdin else Nothing()
        stdout = Just(process.stdout) if process.stdout else Nothing()
        stderr = Just(process.stderr) if process.stderr else Nothing()
        return (stdin, stdout, stderr, process)

    return Io(_inner)


def h_put_str_ln(handle: IO[bytes], string: str) -> Io[None]:
    def _inner():
        handle.write((string + "\n").encode())
        handle.flush()

    return Io(_inner)


def h_get_line(handle: IO[bytes]) -> Io[str]:
    def _inner() -> str:
        return handle.readline().strip().decode()

    return Io(_inner)


def h_get_contents(handle: IO[bytes]):
    def _inner():
        return handle.read().decode()

    return Io(_inner)


def wait_for_process(process: subprocess.Popen) -> Io[int]:
    def _inner() -> int:
        return process.wait()

    return Io(_inner)


# Example usage
if __name__ == "__main__":
    command = "/bin/bash"
    our_shell = create_process(command)

    stdin, stdout, stderr, process = our_shell.run()

    if isinstance(stdin, Just) and isinstance(stdout, Just):
        # set_buffering(stdin.value, io.DEFAULT_BUFFER_SIZE).run()
        # set_buffering(stdout.value, io.DEFAULT_BUFFER_SIZE).run()

        print("Sending pwd")
        h_put_str_ln(stdin.value, "pwd").run()
        print("reading response")
        response = h_get_line(stdout.value).run()
        print(response)

        print("Sending cd test")
        h_put_str_ln(stdin.value, "cd test").run()
        print("reading response")
        # h_get_line(stdout).run() # Not needed, as there is no response

        print("Sending pwd")
        h_put_str_ln(stdin.value, "pwd").run()
        print("reading response")
        response = h_get_line(stdout.value).run()
        print(response)

        h_put_str_ln(stdin.value, "exit").run()
        contents = h_get_contents(stdout.value).run()
        print(contents)

        ec = wait_for_process(process).run()
        print(ec)
