from dataclasses import dataclass
from typing import Iterable, Dict, List, Optional
import ast

@dataclass
class PyIdent:
    module: List[str]
    qual_name: List[str]

class NameEnv:
    def __init__(self, source: str):
        self.env: Dict[str, PyIdent] = self._parse_source(source)

    def _parse_source(self, source: str) -> Dict[str, PyIdent]:
        tree = ast.parse(source)
        ident_dict = {}

        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    module = alias.name
                    ident_dict[alias.asname or alias.name] = PyIdent(
                        module=[module], qual_name=[alias.name]
                    )

            def visit_ImportFrom(self, node):
                module = node.module
                for alias in node.names:
                    qual_name = alias.name
                    ident_dict[alias.asname or alias.name] = PyIdent(
                        module=[module], qual_name=[qual_name]
                    )

            def visit_FunctionDef(self, node):
                qual_name = node.name
                ident_dict[qual_name] = PyIdent(module=[], qual_name=[qual_name])
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                qual_name = node.name
                ident_dict[qual_name] = PyIdent(module=[], qual_name=[qual_name])
                self.generic_visit(node)

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        ident_dict[target.id] = PyIdent(module=[], qual_name=[target.id])
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    ident_dict[node.target.id] = PyIdent(
                        module=[], qual_name=[node.target.id]
                    )
                self.generic_visit(node)

        ImportVisitor().visit(tree)
        return ident_dict

    def get_import_line(self, pyident: PyIdent) -> Optional[str]:
        module_path = ".".join(pyident.module)
        qual_name_path = ".".join(pyident.qual_name)
        if module_path:
            return f"from {module_path} import {qual_name_path}"
        return None

    def get_usage(self, pyident: PyIdent) -> Optional[str]:
        for name, ident in self.env.items():
            if ident == pyident:
                return name
        return None

# Example usage
source_code = """
import os
from collections import namedtuple

def my_function():
    pass

class MyClass:
    def method(self):
        pass

my_var = 10
other_var: int = 20
"""

name_env = NameEnv(source_code)
print("Environment Dictionary:")
for name, ident in name_env.env.items():
    print(f"{name}: {ident}")

# Example PyIdent instances
os_ident = PyIdent(module=["os"], qual_name=["os"])
namedtuple_ident = PyIdent(module=["collections"], qual_name=["namedtuple"])
my_function_ident = PyIdent(module=[], qual_name=["my_function"])
my_class_ident = PyIdent(module=[], qual_name=["MyClass"])
my_var_ident = PyIdent(module=[], qual_name=["my_var"])

# Get import line example
print("\nImport Lines:")
print("Expected: from os import os")
print("Result:  ", name_env.get_import_line(os_ident))

print("Expected: from collections import namedtuple")
print("Result:  ", name_env.get_import_line(namedtuple_ident))

print("Expected: import my_function (should be None because it is not a module import)")
print("Result:  ", name_env.get_import_line(my_function_ident))

print("Expected: import MyClass (should be None because it is not a module import)")
print("Result:  ", name_env.get_import_line(my_class_ident))

print("Expected: import my_var (should be None because it is not a module import)")
print("Result:  ", name_env.get_import_line(my_var_ident))

# Get usage example
print("\nUsages:")
print("Expected: os")
print("Result:  ", name_env.get_usage(os_ident))

print("Expected: namedtuple")
print("Result:  ", name_env.get_usage(namedtuple_ident))

print("Expected: my_function")
print("Result:  ", name_env.get_usage(my_function_ident))

print("Expected: MyClass")
print("Result:  ", name_env.get_usage(my_class_ident))

print("Expected: my_var")
print("Result:  ", name_env.get_usage(my_var_ident))

print("Expected: None (because non_existent is not defined)")
print("Result:  ", name_env.get_usage(PyIdent(module=[], qual_name=["non_existent"])))