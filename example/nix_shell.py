from dataclasses import dataclass
import sys
import os
from pathlib import Path
from typing import Any, Tuple


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.prelude import foldl
from entoli.base.maybe import Just
from entoli.system import create_dir_if_missing, file_exists, write_file
from entoli.process import (
    CreateProcess,
    create_process,
    h_get_contents,
    h_get_line,
    h_put_str_ln,
    read_process_with_exit_code,
    shell,
    terminate_process,
    wait_for_process,
)
from entoli.base.io import Io, put_strln

flake_content = """
{
  description = "A Python 3.12 development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable"; # Switched to unstable for more recent packages
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowUnfree = true; # If necessary for any unfree packages
          };
        };

        pythonEnv = pkgs.python312.withPackages (ps: with ps; [
          ps.pip
        ]);

      in
      {
        devShell = pkgs.mkShell {
          buildInputs = [ pythonEnv ];
          shellHook = ''
            if [ ! -d "venv" ]; then
              echo "Creating a Python virtual environment..."
              ${pythonEnv}/bin/python -m venv venv
            fi

            echo "Activating Python virtual environment..."
            source venv/bin/activate

            if [ ! -f "requirements_dev.txt" ]; then
              echo "Creating a requirements_dev.txt file..."
              touch requirements_dev.txt
            fi
            pip install -r requirements_dev.txt
          '';
        };
      }
    );
}

"""
flake_path = Path(__file__).parent.absolute() / "flake_dir"


# Call nix d
def flake_call(flake_path: Path, cmd: str) -> Io[Tuple[int, str, str]]:
    proc_spec = CreateProcess(
        command=f'nix develop --command bash -c "{cmd}"',
        use_shell=True,
        cwd=Just(flake_path),
    )

    def _inner(tpl) -> Io[Tuple[int, str, str]]:
        match tpl:
            case Just(stdin), Just(stdout), Just(stderr), process:
                return wait_for_process(process).and_then(
                    lambda exit_code: h_get_contents(stdout).and_then(
                        lambda out: h_get_contents(stderr).and_then(
                            lambda err: Io.pure((exit_code, out, err))
                        )
                    )
                )
            case _:
                raise RuntimeError("Failed to create process")

    return create_process(proc_spec).and_then(_inner)


main = (
    create_dir_if_missing(True, flake_path)
    .then(write_file(flake_path / "flake.nix", flake_content))
    .then(put_strln("Flake file created"))
    .then(file_exists(flake_path / "flake.nix"))
    .and_then(lambda res: put_strln(f"Flake file exists: {res}"))
    .then(flake_call(flake_path, "pwd && which python"))
    .and_then(
        lambda res: put_strln(f"exit code: {res[0]}")
        .then(put_strln(f"stdout: {res[1]}"))
        .then(put_strln(f"stderr: {res[2]}"))
    )
)


# def is_walrus_expression(op: Any) -> bool:
#     return isinstance(op, tuple) and len(op) == 2 and isinstance(op[1], Io)


# def do(*ios: Io) -> Io[Any]:
#     def step(acc: Io[Any], op: Any) -> Io[Any]:
#         if isinstance(op, Io):
#             return acc.then(op)
#         elif is_walrus_expression(op):
#             io_action, walrus_op = op
#             return acc.and_then(lambda _: walrus_op).then(io_action)
#         else:
#             return acc.and_then(lambda _: op)

#     return foldl(step, Io.pure(None), ios)


# main = do(
#     create_dir_if_missing(True, flake_path),
#     write_file(flake_path / "flake.nix", flake_content),
#     put_strln("Flake file created"),
#     do(
#         # exists := file_exists(flake_path / "flake.nix"),
#         # put_strln(f"Flake file exists: {exists}"),
#         put_strln(f"Flake file exists: {exists}")
#         for exists in [file_exists(flake_path / "flake.nix")]
#     ),
#     res := flake_call(flake_path, "pwd && which python"),
#     put_strln(f"exit code: {res[0]}"),
#     put_strln(f"stdout: {res[1]}"),
#     put_strln(f"stderr: {res[2]}"),
# )

if __name__ == "__main__":
    main.action()
