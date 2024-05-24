import ast
from dataclasses import dataclass
from email.policy import strict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

from entoli.base.io import Io, put_strln
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.prelude import (
    concat,
    drop,
    elem,
    filter_map,
    find,
    foldl,
    for_each,
    if_else,
    init,
    last,
    length,
    sort_on,
    map,
    filter_,
    head,
    take,
)
from entoli.system import create_dir_if_missing, file_exists, read_file, write_file


@dataclass
class PyIdent:
    module: Iterable[str]
    qual_name: Iterable[str]

    def rel_file_path(self) -> Path:
        path_parts = concat([init(self.module), [last(self.module) + ".py"]])
        return Path(*path_parts)

    def fully_qualified_name(self) -> str:
        return ".".join(concat([self.module, self.qual_name]))

    def import_statement(self) -> str:
        return f"from {self.fully_qualified_name()} import {last(self.qual_name)}"

    def includes(self, other: "PyIdent") -> bool:
        self_fq_name = self.fully_qualified_name()
        stripted_self = if_else(
            self_fq_name.endswith(".*"),
            self_fq_name[:-2],
            self_fq_name,
        )

        return other.fully_qualified_name().startswith(stripted_self)

    def relative_to(self, other: "PyIdent") -> str:
        self_parts = concat([self.module, self.qual_name])
        other_parts = concat([other.module, other.qual_name])

        def _inner(
            self_parts: Iterable[str], other_parts: Iterable[str]
        ) -> Iterable[str]:
            if (
                self_parts == []
                or other_parts == []
                or head(self_parts) != head(other_parts)
            ):
                return self_parts
            else:
                return _inner(init(self_parts), init(other_parts))

        # return _inner(self_parts, other_parts)
        return ".".join(_inner(self_parts, other_parts))


# Compilation takes dependency graph and generates a Io

# # This could be seen as a node of a graph
# @dataclass
# class PyCode:
#     ident: PyIdent
#     code: Iterable[str]


# # SomeParams ... -> PyCode


# # This could be seen as a edge of graphs
# def derive_some_codes(dep_ident0: PyIdent, dep_ident1: PyIdent) -> Iterable[PyCode]: ...


# Need to generate graph from abstract data.
# Which means need to generate nodes and edges.
# Also, it has to be some what modular.
# One unit of should have some amout of information how will it get compiled in to the code.
# This is essential for reusable code generation.

# Dict[PyCode, Iterable[Ident], Iterable[Ident]]


@dataclass
class PyDependecy:
    ident: PyIdent
    is_strict: bool = True
    prefered_last_n: int = 1


DepEnv = Callable[[str], str]


@dataclass
class PyCode:
    ident: PyIdent
    code: Callable[[str, DepEnv], str]  # Assume that the file is already created
    deps: Dict[str, PyDependecy]

    def strict_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(d.is_strict, Just(d.ident), Nothing()), self.deps.values()
        )

    def weak_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(not d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )


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


def validate(codes: Iterable[PyCode]) -> bool:
    def all_idents_unique(codes: Iterable[PyCode]) -> bool:
        idents = map(lambda c: c.ident, codes)

        def is_unique(acc: bool, id: PyIdent) -> bool:
            return acc and (id not in idents)

        return foldl(is_unique, True, idents)

    def all_deps_present(codes: Iterable[PyCode]) -> bool:
        for code in codes:
            # for dep in code.strict_deps + code.weak_deps:
            # for dep in concat([code.strict_deps, code.weak_deps]):
            for dep in code.deps.values():
                if dep not in [c.ident for c in codes]:
                    return False
        return True

    def no_strict_circular_deps(codes: Iterable[PyCode]) -> bool:
        def not_in_circle(visited: Iterable[PyIdent], code: PyCode) -> bool:
            if code.ident in visited:
                return False
            else:
                return all(
                    not_in_circle(concat([visited, [code.ident]]), c)
                    for c in codes
                    if c.ident in code.strict_deps()
                )

        return all(map(lambda c: not_in_circle([], c), codes))

    return (
        all_idents_unique(codes)
        and all_deps_present(codes)
        and no_strict_circular_deps(codes)
    )


def raw_ordered_codes(codes: Iterable[PyCode]) -> Iterable[PyCode]:
    def maybe_free_code(sorted_codes: Iterable[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter_(lambda c: c not in sorted_codes, codes)

        def is_free(code: PyCode) -> bool:
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            # return all(map(lambda i: i in sorted_ids, deps))
            return all(map(lambda i: i.ident in sorted_ids, code.deps.values()))

        free_codes = filter_(is_free, unsorted_codes)

        try:
            # return Just(next(free_codes))
            return Just(head(free_codes))
        except StopIteration:
            return Nothing()

    def maybe_loosely_free_code(sorted_codes: Iterable[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter_(lambda c: c not in sorted_codes, codes)

        def is_loosely_free(code: PyCode) -> bool:
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            return all(map(lambda i: i in sorted_ids, code.strict_deps()))

        free_codes = filter_(is_loosely_free, unsorted_codes)
        less_deps_first = sort_on(lambda c: length(c.weak_deps()), free_codes)

        try:
        except StopIteration:
            return Nothing()

    def _order(acc: Iterable[PyCode], un_ordered: Iterable[PyCode]) -> Iterable[PyCode]:
        if un_ordered == []:
            return acc
        else:
            if m_code := maybe_free_code(acc):
                return _order(concat([acc, [m_code.unwrap()]]), un_ordered)
            elif m_code := maybe_loosely_free_code(acc):
                return _order(concat([acc, [m_code.unwrap()]]), un_ordered)
            else:
                raise RuntimeError("Should be unreachable")

    return _order([], codes)


def ordered_codes(codes: Iterable[PyCode]) -> Maybe[Iterable[PyCode]]:
    if validate(codes):
        return Just(raw_ordered_codes(codes))
    else:
        return Nothing()


def parse_imported_idents(content: str) -> Dict[str, PyIdent]:
    if content == "":
        return {}

    tree = ast.parse(content)
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


def parse_defined_idents(content: str) -> Dict[str, PyIdent]:
    # tree = ast.parse("\n".join(content))
    tree = ast.parse(content)
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


def parse_idents(content: str) -> Tuple[Dict[str, PyIdent], Dict[str, PyIdent]]:
    imported_idents = parse_imported_idents(content)
    module_items = parse_defined_idents(content)
    return imported_idents, module_items


def importing_and_use_as(
    current_module: PyIdent,
    imported_idents: Dict[str, PyIdent],
    defined_idents: Dict[str, PyIdent],
    dep: PyDependecy,
) -> Tuple[Maybe[str], str]:
    if (
        dep.ident.module == current_module.module
    ):  # No need to import, Will be defined in the module
        mb_already_defined = find(lambda i: i[1] == dep, defined_idents.items())
        if mb_already_defined:  # Already defined in the module
            return Nothing(), mb_already_defined.unwrap()[0]
        else:
            raise RuntimeError(
                f"Dependency {dep} should be defined in the module {current_module}, but not found."
            )
    else:  # Dependcy should be imported
        # imported_idents = parse_imported_idents(content)
        mb_already_imported = find(lambda i: i[1] == dep, imported_idents.items())
        if mb_already_imported:
            # No need to check collision with defined idents.
            # Assume there is no error for the given code.
            return Nothing(), mb_already_imported.unwrap()[0]
        else:  # Need to import
            ident_name_parts = concat([dep.ident.module, dep.ident.qual_name])

            def available_last_n(
                defined_idents: Dict[str, PyIdent],
                imported_idents: Dict[str, PyIdent],
                dep: PyIdent,
                prefered_n: int,
            ) -> int:
                importing_parts = take(
                    length(ident_name_parts) - prefered_n + 1, ident_name_parts
                )

                prefered_parts = take(
                    length(ident_name_parts) - prefered_n, ident_name_parts
                )
                prefered_name = ".".join(prefered_parts)

                if not elem(importing_parts, imported_idents) and not elem(
                    head(prefered_parts), defined_idents
                ):
                    return prefered_n
                else:
                    return available_last_n(
                        defined_idents, imported_idents, dep, prefered_n + 1
                    )

            last_n = available_last_n(
                defined_idents, imported_idents, dep.ident, dep.prefered_last_n
            )

            name_to_use = ".".join(
                drop(length(ident_name_parts) - last_n, ident_name_parts)
            )

            import_as = ".".join(
                take(length(ident_name_parts) - last_n + 1, ident_name_parts)
            )

            return Just(import_as), name_to_use


def import_line(ident: PyIdent, importing: str) -> str:

    importing_parts = importing.split(".")
    importing_symbol = last(importing_parts)

    if length(importing_parts) == 1:
        return f"import {importing_symbol}"
    else:
        return f"from {'.'.join(importing_parts[:-1])} import {importing_symbol}"


def append_import_lines(content: str, import_lines: Iterable[str]) -> str:
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
    for line in import_lines:
        lines.insert(import_end, line)
    new_content = "\n".join(lines)
    return new_content


def write_py_code(dir_path: Path, py_code: PyCode) -> Io[None]:
    def _inner(content: str) -> Io[None]:
        imported_idents = parse_imported_idents(content)
        defined_idents = parse_defined_idents(content)

        key_dep_mb_i_us = {
            k: (
                v,
                *importing_and_use_as(
                    py_code.ident, imported_idents, defined_idents, v
                ),
            )
            for k, v in py_code.deps.items()
        }

        dep_mb_i_uss = map(
            lambda dep_mb_i_u: (dep_mb_i_u[0], dep_mb_i_u[1], dep_mb_i_u[2]),
            key_dep_mb_i_us.values(),
        )

        import_lines = filter_map(
            lambda dep_mb_i_us: dep_mb_i_us[1].map(
                lambda i: import_line(dep_mb_i_us[0].ident, i)
            ),
            dep_mb_i_uss,
        )

        def dep_env(dep_name: str) -> str:
            try:
                return key_dep_mb_i_us[dep_name][2]
            except KeyError:
                raise RuntimeError(
                    f"Dependency {dep_name} not found\n, current state of dict: {key_dep_mb_i_us}"
                )

        imported_contents = append_import_lines(content, import_lines)
        new_contents = py_code.code(imported_contents, dep_env)

        return write_file(dir_path / py_code.ident.rel_file_path(), new_contents)

    file_path = dir_path / py_code.ident.rel_file_path()

    return (
        put_strln(f"\nWriting {py_code.ident.qual_name } to {file_path}\n")
        .then(file_exists(file_path))
        .and_then(
            lambda exists: if_else(
                exists,
                Io.pure(None),
                create_dir_if_missing(True, file_path.parent).then(
                    write_file(file_path, "")
                ),
            )
        )
        .then(read_file(file_path))
        .and_then(_inner)
    )
