import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli import base
from entoli.base.maybe import Just
from entoli.base.io import Io, put_strln, get_str
from entoli.prelude import foldl, for_each
from entoli.system import (
    call_command,
    create_dir,
    create_dir_if_missing,
    create_process,
    h_get_contents,
    h_get_line,
    h_put_str_ln,
    shell,
    write_file,
)


python_flake_lines = """
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


def setup_python(dir_path: Path) -> Io[None]:
    # bash = shell("/bin/bash")
    bash = 


    def _main(tpl) -> Io[None]:
        match tpl:
            case Just(stdin), Just(stdout), Just(stderr), process:
                return (
                    create_dir_if_missing(True, dir_path)
                    .then(write_file(dir_path / ".envrc", "use flake"))
                    .then(write_file(dir_path / "flake.nix", python_flake_lines))
                    .then(h_put_str_ln(stdin, f"cd {dir_path}"))
                    .then(h_put_str_ln(stdin, "direnv allow"))
                    .then(h_put_str_ln(stdin, f"cd {dir_path}"))
                    .then(h_get_contents(stdout))
                    .and_then(
                        lambda lines: foldl(
                            lambda acc, line: acc.then(put_strln(line)),
                            put_strln(""),
                            lines,
                        )
                    )
                )
            case _:
                raise RuntimeError("Failed to create process")

    return create_process(bash).and_then(_main)


main = setup_python(Path(__file__).parent / "generated_python_dev")

if __name__ == "__main__":
    main.action()
