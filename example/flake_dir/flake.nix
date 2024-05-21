
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

