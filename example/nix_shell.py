import sys
import os
from pathlib import Path
from typing import Any, Tuple


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.base.maybe import Just
from entoli.system import create_dir_if_missing, file_exists, write_file
from entoli.process import (
    CreateProcess,
    create_process,
    h_get_contents,
    wait_for_process,
)
from entoli.prelude import unlines, put_strln
from entoli.base.io import Io

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
flake_path = Path(__file__).parent.absolute() / "build"


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
    .then(file_exists(flake_path / "flake.nix"))
    .and_then(lambda res: put_strln(f"Flake file exists: {res}"))
    .then(write_file(flake_path / ".envrc", "use flake"))
    .then(file_exists(flake_path / ".envrc"))
    .and_then(lambda res: put_strln(f"Envrc file exists: {res}"))
    .then(flake_call(flake_path, "pwd && which python"))
    .then(
        flake_call(
            flake_path,
            unlines(
                [
                    "pip install django",
                    "django-admin --version",
                    "django-admin startproject auto_project",
                    "cd auto_project",
                    "python manage.py startapp auto_app_0",
                    "python manage.py startapp auto_app_1",
                    "python manage.py makemigrations",
                    "python manage.py migrate",
                    "export DJANGO_SUPERUSER_USERNAME=admin",
                    "export DJANGO_SUPERUSER_EMAIL=a@a.com",
                    "export DJANGO_SUPERUSER_PASSWORD=admin",
                    "python manage.py createsuperuser --noinput",
                ]
            ),
        )
    )
    .and_then(
        lambda res: put_strln(f"exit code: {res[0]}")
        .then(put_strln(f"stdout: {res[1]}"))
        .then(put_strln(f"stderr: {res[2]}"))
    )
)

if __name__ == "__main__":
    main.action()
