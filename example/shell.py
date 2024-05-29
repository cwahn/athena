import sys
import os
from pathlib import Path


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.base.maybe import Just
from entoli.process import (
    create_process,
    h_get_contents,
    h_get_line,
    h_put_str_ln,
    shell,
    terminate_process,
    wait_for_process,
)
from entoli.base.io import Io
from entoli.prelude import put_strln


def _main(tpl) -> Io[None]:
    match tpl:
        case Just(stdin), Just(stdout), Just(stderr), process:
            return (
                h_put_str_ln(stdin, "pwd")
                .then(h_get_line(stdout))
                .and_then(lambda pwd: put_strln(f"pwd: {pwd}"))
                .then(h_put_str_ln(stdin, f"cd {Path(__file__).parent}"))
                .then(put_strln("cd to example"))
                .then(h_put_str_ln(stdin, "pwd"))
                .then(h_get_line(stdout))
                .and_then(lambda pwd: put_strln(f"pwd: {pwd}"))
                .then(terminate_process(process))
                .then(wait_for_process(process))
                .and_then(lambda exit_code: put_strln(f"exit code: {exit_code}"))
                .then(h_get_contents(stdout))
                .and_then(lambda out: put_strln(f"stdout: {out}"))
            )
        case _:
            raise RuntimeError("Failed to create process")


main = create_process(shell("/bin/zsh")).and_then(_main)

if __name__ == "__main__":
    main.action()
