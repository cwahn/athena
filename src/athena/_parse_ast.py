import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Union


@dataclass
class PyIdent:
    module: List[str]
    qual_name: List[str]

    def re_file_path(self) -> Path:
        return Path(*self.module) / Path(*self.qual_name) / Path("__init__.py")

    def fully_qualified_name(self) -> str:
        return ".".join(self.module + self.qual_name)

    def import_statement(self) -> str:
        return f"from {self.fully_qualified_name()} import {self.qual_name[-1]}"


def parse_imports(lines: List[str]) -> Dict[str, PyIdent]:
    tree = ast.parse("\n".join(lines))
    imports = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name_parts = alias.name.split(".")
                ident = PyIdent(module=[], qual_name=name_parts)
                asname = alias.asname if alias.asname else name_parts[0]
                imports[asname] = ident
        elif isinstance(node, ast.ImportFrom):
            module_parts = node.module.split(".") if node.module else []
            for alias in node.names:
                qual_name = module_parts + [alias.name]
                ident = PyIdent(module=module_parts, qual_name=[alias.name])
                asname = alias.asname if alias.asname else alias.name
                imports[asname] = ident

    return imports


def parse_module_items(lines: List[str]) -> Dict[str, PyIdent]:
    tree = ast.parse("\n".join(lines))
    module_items = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            qual_name = [node.name]
            ident = PyIdent(module=[], qual_name=qual_name)
            module_items[node.name] = ident
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    qual_name = [target.id]
                    ident = PyIdent(module=[], qual_name=qual_name)
                    module_items[target.id] = ident
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                qual_name = [node.target.id]
                ident = PyIdent(module=[], qual_name=qual_name)
                module_items[node.target.id] = ident

    return module_items


# Example usage
if __name__ == "__main__":
    source_code = [
        "import os",
        "import sys as system",
        "from collections import namedtuple",
        "from mypackage.subpackage import mymodule as mm",
        "",
        "def my_function():",
        "    pass",
        "",
        "class MyClass:",
        "    pass",
        "",
        "my_variable = 42",
        "my_other_variable: int = 10",
    ]

    imports = parse_imports(source_code)
    module_items = parse_module_items(source_code)

    print("Imports:")
    for key, value in imports.items():
        print(f"{key}: {value}")
        print(f"  Import Statement: {value.import_statement()}")
        print(f"  Fully Qualified Name: {value.fully_qualified_name()}")
        print(f"  File Path: {value.re_file_path()}")

    print("\nModule Items:")
    for key, value in module_items.items():
        print(f"{key}: {value}")
        print(f"  Fully Qualified Name: {value.fully_qualified_name()}")
        print(f"  File Path: {value.re_file_path()}")
