from dataclasses import dataclass
from typing import Iterable, Dict, List
import ast


@dataclass
class PyIdent:
    module: List[str]
    qual_name: List[str]


def name_env_from_src(source: str) -> Dict[str, PyIdent]:
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


# Example usage
src = """
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

name_env = name_env_from_src(src)
for name, ident in name_env.items():
    print(f"{name}: {ident}")
