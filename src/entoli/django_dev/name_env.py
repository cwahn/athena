import pytest
from dataclasses import dataclass
from typing import Iterable, Dict, List, Optional, Self
import ast

from entoli.base.maybe import Just, Maybe, Nothing
from entoli.django_dev.py_code import PyIdent


@dataclass
class NameEnv:
    env: Dict[str, PyIdent]

    @staticmethod
    def from_source(source: str) -> "NameEnv":
        tree = ast.parse(source)
        ident_dict: Dict[str, PyIdent] = {}

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
                        ident_dict[target.id] = PyIdent(
                            module=[], qual_name=[target.id]
                        )
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    ident_dict[node.target.id] = PyIdent(
                        module=[], qual_name=[node.target.id]
                    )
                self.generic_visit(node)

        ImportVisitor().visit(tree)
        return NameEnv(ident_dict)

    def get_import_line(self, pyident: PyIdent) -> Maybe[str]:
        module_path = ".".join(pyident.module)
        qual_name_path = ".".join(pyident.qual_name)
        if module_path:
            # return f"from {module_path} import {qual_name_path}"
            return Just(f"from {module_path} import {qual_name_path}")
        # return None
        return Nothing()

    def get_usage(self, pyident: PyIdent) -> Maybe[str]:
        for name, ident in self.env.items():
            if ident == pyident:
                # return name
                return Just(name)
            if ident.module and pyident.module and ident.module[0] == pyident.module[0]:
                # return f"{ident.module[0]}.{'.'.join(pyident.qual_name)}"
                return Just(f"{ident.module[0]}.{'.'.join(pyident.qual_name)}")
        # return None
        return Nothing()


# In-file pytest tests
def test_get_import_line():
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
import models
"""
    name_env = NameEnv.from_source(source_code)

    os_ident = PyIdent(module=["os"], qual_name=["os"])
    namedtuple_ident = PyIdent(module=["collections"], qual_name=["namedtuple"])
    my_function_ident = PyIdent(module=[], qual_name=["my_function"])
    my_class_ident = PyIdent(module=[], qual_name=["MyClass"])
    my_var_ident = PyIdent(module=[], qual_name=["my_var"])
    char_field_ident = PyIdent(module=["models"], qual_name=["CharField"])

    # assert name_env.get_import_line(os_ident) == "from os import os"
    assert name_env.get_import_line(os_ident) == Just("from os import os")
    # assert (
    #     name_env.get_import_line(namedtuple_ident)
    #     == "from collections import namedtuple"
    # )
    assert name_env.get_import_line(namedtuple_ident) == Just(
        "from collections import namedtuple"
    )
    # assert name_env.get_import_line(my_function_ident) is None
    assert name_env.get_import_line(my_function_ident) == Nothing()
    # assert name_env.get_import_line(my_class_ident) is None
    assert name_env.get_import_line(my_class_ident) == Nothing()
    # assert name_env.get_import_line(my_var_ident) is None
    assert name_env.get_import_line(my_var_ident) == Nothing()


def test_get_usage():
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
import models
"""
    name_env = NameEnv.from_source(source_code)

    os_ident = PyIdent(module=["os"], qual_name=["os"])
    namedtuple_ident = PyIdent(module=["collections"], qual_name=["namedtuple"])
    my_function_ident = PyIdent(module=[], qual_name=["my_function"])
    my_class_ident = PyIdent(module=[], qual_name=["MyClass"])
    my_var_ident = PyIdent(module=[], qual_name=["my_var"])
    char_field_ident = PyIdent(module=["models"], qual_name=["CharField"])

    # assert name_env.get_usage(os_ident) == "os"
    assert name_env.get_usage(os_ident) == Just("os")
    # assert name_env.get_usage(namedtuple_ident) == "namedtuple"
    assert name_env.get_usage(namedtuple_ident) == Just("namedtuple")
    # assert name_env.get_usage(my_function_ident) == "my_function"
    assert name_env.get_usage(my_function_ident) == Just("my_function")
    # assert name_env.get_usage(my_class_ident) == "MyClass"
    assert name_env.get_usage(my_class_ident) == Just("MyClass")
    # assert name_env.get_usage(my_var_ident) == "my_var"
    assert name_env.get_usage(my_var_ident) == Just("my_var")
    # assert name_env.get_usage(PyIdent(module=[], qual_name=["non_existent"])) is None
    assert (
        name_env.get_usage(PyIdent(module=[], qual_name=["non_existent"])) == Nothing()
    )
    # assert name_env.get_usage(char_field_ident) == "models.CharField"
    assert name_env.get_usage(char_field_ident) == Just("models.CharField")


# # Run the tests if the script is executed directly
# if __name__ == "__main__":
#     import pytest

#     pytest.main([__file__])
