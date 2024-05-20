import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from entoli.base.io import Io, put_strln
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.prelude import (
    concat,
    foldl,
    for_each,
    sort_on,
    map,
    filter,
    head,
)
from entoli.system import create_dir_if_missing, file_exists, read_file, write_file


@dataclass
class PyIdent:
    module: List[str]
    qual_name: List[str]

    def file_path(self) -> Path:
        # Add .py
        path_parts = self.module[:-1] + [self.module[-1] + ".py"]
        return Path(*path_parts)

    def fully_qualified_name(self) -> str:
        return ".".join(self.module + self.qual_name)

    def import_statement(self) -> str:
        return f"from {self.fully_qualified_name()} import {self.qual_name[-1]}"


# Compilation takes dependency graph and generates a Io

# # This could be seen as a node of a graph
# @dataclass
# class PyCode:
#     ident: PyIdent
#     code: List[str]


# # SomeParams ... -> PyCode


# # This could be seen as a edge of graphs
# def derive_some_codes(dep_ident0: PyIdent, dep_ident1: PyIdent) -> List[PyCode]: ...


# Need to generate graph from abstract data.
# Which means need to generate nodes and edges.
# Also, it has to be some what modular.
# One unit of should have some amout of information how will it get compiled in to the code.
# This is essential for reusable code generation.

# Dict[PyCode, List[Ident], List[Ident]]


@dataclass
class PyCode:
    ident: PyIdent
    code: List[str]
    strict_deps: List[PyIdent]
    weak_deps: List[PyIdent]


# Validation
# 1. No duplicate identifiers
# 2. All strict and weak deps should be in the code.
# 3. No circular dependencies through strict deps

# Sorting
# 1. All the strict deps should comes first
# 2. All the weak deps should
# 3. At any point, if there is unsorted code, whoose all strict deps are sorted, should be present asap.
# Which means, code with no deps should comes first.
# After that code with only weak deps should comes.
# After adding code only with weak deps re do the process.


def validate(codes: List[PyCode]) -> bool:
    def all_idents_unique(codes: List[PyCode]) -> bool:
        idents = map(lambda c: c.ident, codes)

        def is_unique(acc: bool, id: PyIdent) -> bool:
            return acc and (id not in idents)

        return foldl(is_unique, True, idents)

    def all_deps_present(codes: List[PyCode]) -> bool:
        for code in codes:
            for dep in code.strict_deps + code.weak_deps:
                if dep not in [c.ident for c in codes]:
                    return False
        return True

    def no_strict_circular_deps(codes: List[PyCode]) -> bool:
        def not_in_circle(visited: List[PyIdent], code: PyCode) -> bool:
            if code.ident in visited:
                return False
            else:
                return all(
                    not_in_circle(visited + [code.ident], c)
                    for c in codes
                    if c.ident in code.strict_deps
                )

        return all(map(lambda c: not_in_circle([], c), codes))

    return (
        all_idents_unique(codes)
        and all_deps_present(codes)
        and no_strict_circular_deps(codes)
    )


def raw_ordered_codes(codes: List[PyCode]) -> List[PyCode]:
    def maybe_free_code(sorted_codes: List[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter(lambda c: c not in sorted_codes, codes)

        def is_free(code: PyCode) -> bool:
            deps = concat([code.strict_deps, code.weak_deps])
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            return all(map(lambda i: i in sorted_ids, deps))

        free_codes = filter(is_free, unsorted_codes)

        try:
            # return Just(next(free_codes))
            return Just(head(free_codes))
        except StopIteration:
            return Nothing()

    def maybe_loosely_free_code(sorted_codes: List[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter(lambda c: c not in sorted_codes, codes)

        def is_loosely_free(code: PyCode) -> bool:
            # sorted_ids = [c.ident for c in sorted_codes]
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            # return all((i in sorted_ids) for i in code.strict_deps)
            return all(map(lambda i: i in sorted_ids, code.strict_deps))

        free_codes = filter(is_loosely_free, unsorted_codes)
        less_deps_first = sort_on(lambda c: len(c.weak_deps), free_codes)

        try:
            # return Just(next(less_deps_first))
            return Just(head(less_deps_first))
        except StopIteration:
            return Nothing()

    def _order(acc: List[PyCode], un_ordered: List[PyCode]) -> List[PyCode]:
        if un_ordered == []:
            return acc
        else:
            if m_code := maybe_free_code(acc):
                return _order(acc + [m_code.unwrap()], un_ordered)
            elif m_code := maybe_loosely_free_code(acc):
                return _order(acc + [m_code.unwrap()], un_ordered)
            else:
                raise RuntimeError("Should be unreachable")

    return _order([], codes)


def ordered_codes(codes: List[PyCode]) -> Maybe[List[PyCode]]:
    if validate(codes):
        return Just(raw_ordered_codes(codes))
    else:
        return Nothing()


# def write_py_code(py_code: PyCode) -> Io[None]: ...

# 1. Check if module file exists
# 2. If exists, get all the identifiers imported and defined in module space. Collect both module, qual_name and used form.
# 3. Make import statement of the depedencies from the info.
# If the same depenency is already imported, then don't import it again.
# Otherwise, import it, after determining the used form to avoid name conflicts.
# 4. Then write the definition of the code with the import used form.

# @dataclass
# class PyIdent:
#     module: List[str]
#     qual_name: List[str]

#     def re_file_path(self) -> Path:
#         return Path(*self.module) / Path(*self.qual_name) / Path("__init__.py")

#     def fulley_qualified_name(self) -> str:
#         return ".".join(self.module + self.qual_name)

#     def import_statement(self) -> str:
#         return f"from {self.fulley_qualified_name()} import {self.qual_name[-1]}"


def parse_imported_idents(lines: List[str]) -> Dict[str, PyIdent]:
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


def parse_defined_idents(lines: List[str]) -> Dict[str, PyIdent]:
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


def parse_idents(lines: List[str]) -> Tuple[Dict[str, PyIdent], Dict[str, PyIdent]]:
    imported_idents = parse_imported_idents(lines)
    module_items = parse_defined_idents(lines)
    return imported_idents, module_items


def existing_idents(path: Path) -> Io[Tuple[Dict[str, PyIdent], Dict[str, PyIdent]]]:
    return read_file(path).map(
        lambda string: (lines := string.split("\n"), parse_idents(lines))[-1]
    )


def import_as(
    imported_idents: Dict[str, PyIdent],
    defined_idents: Dict[str, PyIdent],
    ident: PyIdent,
) -> Maybe[str]:
    # If the same one is already imported, skip
    if ident in imported_idents.values():
        return Nothing()

    base_name = ident.qual_name[-1]
    if base_name not in defined_idents and base_name not in imported_idents:
        return Just(base_name)

    # Add module parts to the base name to avoid collision
    for i in range(1, len(ident.module) + 1):
        qualified_name = "_".join(ident.module[-i:] + ident.qual_name)
        if (
            qualified_name not in defined_idents
            and qualified_name not in imported_idents
        ):
            return Just(qualified_name)

    # If still colliding, return fully qualified name
    return Just(ident.fully_qualified_name())


def import_line(ident: PyIdent, import_as: str) -> str:
    is_module = len(ident.qual_name) == 0
    if is_module:
        need_as = ".".join(ident.module) != import_as
        if need_as:
            return f"import {ident.module[-1]} as {import_as}"
        else:
            return f"import {ident.module[-1]}"
    else:  # item in module
        need_as = ".".join(ident.qual_name) != import_as
        if need_as:
            return f"from {".".join(ident.module)} import {".".join(ident.qual_name)} as {import_as}"
        else:
            return f"from {".".join(ident.module)} import {".".join(ident.qual_name)}"


def deps_import_lines(
    existing_idents: Dict[str, PyIdent],
    defined_idents: Dict[str, PyIdent],
    py_code: PyCode,
) -> List[str]:
    return list(
        map(
            lambda dep: (
                import_as_ := import_as(existing_idents, defined_idents, dep),
                import_line(dep, import_as_.unwrap()) if import_as_ else "",
            )[-1],
            py_code.strict_deps + py_code.weak_deps,
        )
    )


def append_import_lines(path: Path, import_lines: List[str]) -> Io[None]:
    def _inner(content: str) -> Io[None]:
        lines = content.split("\n")
        # Find the end of the import statements
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_end = i + 1
            elif line.strip() == "":
                continue
            else:
                break

        # Insert the new import line at the end of the imports
        for_each(lambda line: lines.insert(import_end, line), import_lines)
        new_content = "\n".join(lines)
        return write_file(path, new_content)

    return read_file(path).and_then(_inner)


def append_definition_lines(path: Path, def_lines: List[str]) -> Io[None]:
    def _inner(content: str) -> Io[None]:
        lines = content.split("\n")

        new_lines = concat([lines, ["\n"], def_lines])

        new_content = "\n".join(new_lines)
        return write_file(path, new_content)

    return read_file(path).and_then(_inner)


def write_py_code(py_code: PyCode) -> Io[None]:
    file_path = py_code.ident.file_path()

    return (
        put_strln(f"\nWriting {py_code.ident.qual_name } to {file_path}\n")
        .then(file_exists(file_path))
        .and_then(
            lambda exists: Io.pure(None)
            if exists
            else create_dir_if_missing(True, file_path.parent).then(
                write_file(file_path, "")
            )
        )
        .and_then(
            lambda _: existing_idents(file_path).and_then(
                lambda idents: (
                    imported_idents := idents[0],
                    defined_idents := idents[1],
                    deps_import_lines_ := deps_import_lines(
                        imported_idents, defined_idents, py_code
                    ),
                    append_import_lines(file_path, deps_import_lines_).then(
                        append_definition_lines(file_path, py_code.code)
                    ),
                )[-1]
            )
        )
    )
