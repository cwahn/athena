import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.base.maybe import Just
from entoli.prelude import foldl
from entoli.system import (
    call_command,
    create_dir,
    create_process,
    h_get_line,
    h_put_str_ln,
    shell,
    write_file,
)

from entoli.base.io import Io, put_strln, get_str
from entoli.base.control import delay_for, loop


# make_build_dir = create_dir(Path("build"))
# start_project = call_command("cd build && django-admin startproject mysite")

# main = foldl(
#     lambda acc, io: acc.then(io), Io.pure(None), [make_build_dir, start_project]
# )


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
            )
        case _:
            raise RuntimeError("Failed to create process")


main = create_process(shell("/bin/zsh")).and_then(_main) 

if __name__ == "__main__":
    main.action()
