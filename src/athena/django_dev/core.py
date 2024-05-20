# Prerequsites: In venv with Django installed, run the following commands:

from pathlib import Path
from athena.base.io import Io
from athena.system import call_command


# def start_project(project_name: str) -> Io[None]:
#     return call_command(f"django-admin startproject {project_name}")

# def start_app(app_name: str) -> Io[None]:
#     return call_command(f"python manage.py startapp {app_name}")

def start_project(root_dir: Path, project_name: str) -> Io[None]:
    return call_command(f"django-admin startproject {project_name}", cwd=root_dir)