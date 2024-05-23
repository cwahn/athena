import ast
from dataclasses import dataclass
import importlib
from typing import Callable, Iterable, Dict, Tuple

from pytest import Item

from entoli.base.maybe import Just, Nothing, Maybe
from entoli.py_code.py_ident import PyIdent
from entoli.map import Map
from entoli.prelude import (
    concat,
    filter_map,
    conditioanl,
    fst,
    head,
    is_prefix_of,
    is_suffix_of,
    length,
    snd,
)


@dataclass
class PyDependecy:
    ident: PyIdent
    is_strict: bool = True


@dataclass
class IdEnv:
    env: Dict[str, PyIdent]

    def __call__(self, name: str) -> str:
        return self.env[name].full_qual_name()

    @staticmethod
    def from_file(file_module: Iterable[str], src: str) -> "IdEnv":
        tree = ast.parse(src)
        env_map = {}

        class Visitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    module = alias.name
                    env_map[alias.asname or alias.name] = PyIdent(
                        module=[module], mb_name=Just(alias.name)
                    )

            def visit_ImportFrom(self, node):
                match node.module:
                    case None:
                        module_parts = []
                    case md:
                        module_parts = md.split(".")

                if "*" in [alias.name for alias in node.names]:
                    try:
                        imported_module = importlib.import_module(node.module)
                        for attr in dir(imported_module):
                            if not attr.startswith("_"):
                                env_map[attr] = PyIdent(
                                    module=module_parts, mb_name=Just(attr)
                                )
                    except ImportError:
                        pass

                else:
                    for alias in node.names:
                        qual_name = alias.name
                        env_map[alias.asname or alias.name] = PyIdent(
                            module=module_parts, mb_name=Just(qual_name)
                        )

            def visit_FunctionDef(self, node):
                qual_name = node.name
                env_map[qual_name] = PyIdent(
                    module=list(file_module), mb_name=Just(qual_name)
                )
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                qual_name = node.name
                env_map[qual_name] = PyIdent(
                    module=list(file_module), mb_name=Just(qual_name)
                )
                self.generic_visit(node)

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        env_map[target.id] = PyIdent(
                            module=list(file_module), mb_name=Just(target.id)
                        )
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    env_map[node.target.id] = PyIdent(
                        module=list(file_module), mb_name=Just(node.target.id)
                    )
                self.generic_visit(node)

        Visitor().visit(tree)
        return IdEnv(env_map)


# Define the test class using pytest
class TestIdEnv:
    def test_from_file(self):
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
        file_module = ["test_module"]
        id_env = IdEnv.from_file(file_module, source_code)

        assert id_env("os") == "os.os"
        assert id_env("namedtuple") == "collections.namedtuple"
        assert id_env("my_function") == "test_module.my_function"
        assert id_env("MyClass") == "test_module.MyClass"
        assert id_env("my_var") == "test_module.my_var"
        assert id_env("other_var") == "test_module.other_var"


@dataclass
class PyCode:
    ident: PyIdent
    code: Callable[[str, IdEnv], str]  # Assume that the file is already created
    deps: Map[str, PyDependecy]

    def strict_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: conditioanl(d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )

    def weak_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: conditioanl(not d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )
