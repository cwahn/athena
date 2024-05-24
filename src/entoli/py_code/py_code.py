import ast
from dataclasses import dataclass
import importlib
from typing import Callable, Iterable, Dict
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.map import Map
from entoli.prelude import (
    elem,
    map,
    filter,
    concat,
    filter_map,
    find,
    foldl,
    if_else,
    fst,
    head,
    is_prefix_of,
    is_suffix_of,
    last,
    length,
    snd,
    init,
    sort_on,
    tail,
    unique,
)


@dataclass
class PyIdent:
    module: Iterable[str]
    mb_name: Maybe[str]

    def module_name(self) -> str:
        return ".".join(self.module)

    def full_qual_name(self) -> str:
        match self.mb_name:
            case Nothing():
                return self.module_name()
            case Just(name):
                return f"{self.module_name()}.{name}"

    def full_qual_name_parts(self) -> Iterable[str]:
        match self.mb_name:
            case Nothing():
                return self.module
            case Just(name):
                return concat([self.module, [name]])

    def is_module(self) -> bool:
        match self.mb_name:
            case Nothing():
                return True
            case Just(_):
                return False

    def is_wildcard(self) -> bool:
        # return is_suffix_of(".*", self.full_qual_name())
        return is_suffix_of(["*"], self.full_qual_name_parts())

    def includes(self, other: "PyIdent") -> bool:
        wc_striped = if_else(
            tail(self.full_qual_name_parts()) == ["*"],
            init(self.full_qual_name_parts()),
            self.full_qual_name_parts(),
        )

        other_parts = other.full_qual_name_parts()

        if length(wc_striped) > length(other_parts):
            return False
        else:
            return is_prefix_of(wc_striped, other_parts)

    def relative_name_to(self, other: "PyIdent") -> Maybe[str]:
        def _relative_name_to(
            self_part: Iterable[str], other_part: Iterable[str]
        ) -> Maybe[str]:
            match self_part:
                case []:
                    # raise ValueError(
                    #     f"Name of {self} is not longer than other. Cannot be referred relative to {other}."
                    # )
                    return Nothing()
                case [self_head, *self_tail]:
                    match other_part:
                        case []:
                            # return ".".join(self_part)
                            return Just(".".join(self_part))
                        case [other_head, *other_tail]:
                            if self_head != other_head:
                                # return ".".join(self_part)
                                return Just(".".join(self_part))
                            else:
                                return _relative_name_to(self_tail, other_tail)

            raise RuntimeError("Unreachable code")

        return _relative_name_to(
            self.full_qual_name_parts(), other.full_qual_name_parts()
        )

    def refered_as_in(self, name_env: "IdEnv") -> str:
        relevant_env = filter_map(
            lambda key_id: if_else(snd(key_id).includes(self), Just(key_id), Nothing()),
            name_env.inner.items(),
        )

        if length(relevant_env) == 0:
            raise ValueError(f"No relevant env for {self}, not defined or included.")
        elif length(relevant_env) > 1:
            raise ValueError(
                f"Multiple relevant env for {self}, {relevant_env}. Ambiguous."
            )
        else:
            relevant_ident = snd(head(relevant_env))
            relevent_key = fst(head(relevant_env))
            if self == relevant_ident:  # exact import or definition
                return relevent_key
            else:  # partial import
                return (
                    relevent_key + "." + self.relative_name_to(relevant_ident).unwrap()
                )

    def mb_import_line(self, id_env: "IdEnv") -> Maybe[str]:
        if self.module == []:  # In-file definition, no need to import
            return Nothing()
        else:
            mb_relevent = find(
                lambda key_id: snd(key_id).includes(self), id_env.inner.items()
            )
            if mb_relevent:  # Maybe already imported
                return Nothing()
            else:  # Need to get imported
                if not self.mb_name:  # Self is a module
                    if length(self.module) == 1:
                        modeule_name = head(self.module)
                        if modeule_name in id_env.inner:
                            return Just(f"import {modeule_name} as {modeule_name}_")
                        else:
                            return Just(f"import {modeule_name}")
                    else:  # try to use from import
                        last_module_name = last(self.module)
                        if last_module_name not in id_env.inner:  # No conflict
                            # todo Actually in case of item with the same name with the module, it could be not a conflict.
                            return Just(
                                f"from {init(self.module)} import {last_module_name}"
                            )
                        else:  # Conflict
                            return Just(
                                f"from {init(self.module)} import {last_module_name} as {last_module_name}_"
                            )
                else:  # Self is a name in a module
                    fully_qualified = self.full_qual_name_parts()
                    last_name = last(fully_qualified)
                    if last_name not in id_env.inner:
                        return Just(f"from {init(fully_qualified)} import {last_name}")
                    else:
                        return Just(
                            f"from {init(fully_qualified)} import {last_name} as {last_name}_"
                        )


# In-file pytest tests


class _TestPyIdent:
    def _test_PyIdent_construct(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.module == ["os"]
        assert ident.mb_name == Just("os")

        ident = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.module == ["os"]
        assert ident.mb_name == Nothing()

    def _test_PyIdent_full_qual_name(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.full_qual_name() == "os.os"

        ident = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.full_qual_name() == "os"

    def _test_PyIdent_full_qual_name_parts(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.full_qual_name_parts() == ["os", "os"]

        ident = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.full_qual_name_parts() == ["os"]

    def _test_PyIdent_is_module(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert not ident.is_module()

        ident = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.is_module()

    def _test_PyIdent_is_wildcard(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert not ident.is_wildcard()

        ident = PyIdent(module=["os"], mb_name=Nothing())
        assert not ident.is_wildcard()

        ident = PyIdent(module=["os"], mb_name=Just("*"))
        assert ident.is_wildcard()

        # Not considering qualified names.
        # This is for module-level or upper.
        # ident = PyIdent(module=["os"], mb_name=Just("os.*"))
        # assert ident.is_wildcard()

    def _test_PyIdent_includes(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        other = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.includes(other)

        # Not considering qualified names.
        # This is for module-level or upper.

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        other = PyIdent(module=["os"], mb_name=Nothing())
        assert not ident.includes(other)

        ident = PyIdent(module=["os"], mb_name=Nothing())
        other = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.includes(other)

        # ident = PyIdent(module=["os"], mb_name=Just("os"))
        # other = PyIdent(module=["os"], mb_name=Just("os.path"))
        # assert ident.includes(other)

        # ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        # other = PyIdent(module=["os"], mb_name=Just("os"))
        # assert not ident.includes(other)

        # ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        # other = PyIdent(module=["os"], mb_name=Just("os.path"))
        # assert ident.includes(other)

        # ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        # other = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        # assert ident.includes(other)

        # ident = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        # other = PyIdent(module=["os"], mb_name=Just("os.path"))
        # assert not ident.includes(other)

    def _test_PyIdent_relative_name_to(self):
        # Qualified names are not considered.
        # This is for module-level or upper.

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        other = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.relative_name_to(other) == Just("os")

        ident = PyIdent(module=["os"], mb_name=Nothing())
        other = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.relative_name_to(other) == Nothing()

        ident = PyIdent(module=["os"], mb_name=Nothing())
        other = PyIdent(module=["os", "path"], mb_name=Just("path"))
        assert ident.relative_name_to(other) == Nothing()

        ident = PyIdent(module=["os", "path"], mb_name=Just("path"))
        other = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.relative_name_to(other) == Just("path.path")

    def _test_PyIdent_inverse_name_env(self):
        name_env = IdEnv(
            inner=Map(
                [
                    ("os", PyIdent(module=["os"], mb_name=Just("os"))),
                    ("os.path", PyIdent(module=["os"], mb_name=Just("os.path"))),
                    (
                        "os.path.join",
                        PyIdent(module=["os"], mb_name=Just("os.path.join")),
                    ),
                ]
            )
        )

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.refered_as_in(name_env) == "os"

        ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        assert ident.refered_as_in(name_env) == "os.path"

        ident = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        assert ident.refered_as_in(name_env) == "os.path.join"

    def _test_PyIdent_mb_import_line(self):
        name_env = IdEnv(
            inner=Map(
                [
                    ("os", PyIdent(module=["os"], mb_name=Just("os"))),
                    ("os.path", PyIdent(module=["os"], mb_name=Just("os.path"))),
                    (
                        "os.path.join",
                        PyIdent(module=["os"], mb_name=Just("os.path.join")),
                    ),
                ]
            )
        )

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.mb_import_line(name_env) == Nothing()

        # todo Name of item the same with the module name need to be handled.
        # ident = PyIdent(module=["os"], mb_name=Nothing())
        # assert ident.mb_import_line(name_env) == Just("import os")

        # ! Qualified names are not considered. PyIdent is for module-level item of upper.
        # ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        # assert ident.mb_import_line(name_env) == Just("from os import path")

        # ident = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        # assert ident.mb_import_line(name_env) == Just("from os.path import join")

        # ident = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        # name_env = IdEnv(
        #     inner=Map(
        #         [
        #             ("os", PyIdent(module=["os"], mb_name=Just("os"))),
        #             ("os.path", PyIdent(module=["os"], mb_name=Just("os.path"))),
        #             (
        #                 "os.path.join",
        #                 PyIdent(module=["os"], mb_name=Just("os.path.join")),
        #             ),
        #             ("join", PyIdent(module=["os", "path"], mb_name=Just("join"))),
        #         ]
        #     )
        # )
        # assert ident.mb_import_line(name_env) == Just(
        #     "from os.path import join as join_"
        # )


@dataclass
class PyDependecy:
    ident: PyIdent
    is_strict: bool = True


@dataclass
class IdEnv:
    inner: Map[str, PyIdent]

    def __call__(self, name: str) -> str:
        return self.inner[name].full_qual_name()

    @staticmethod
    def from_file(src: str) -> "IdEnv":
        tree = ast.parse(src)
        env_map = Map([])

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
                env_map[qual_name] = PyIdent(module=list([]), mb_name=Just(qual_name))
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                qual_name = node.name
                env_map[qual_name] = PyIdent(module=list([]), mb_name=Just(qual_name))
                self.generic_visit(node)

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        env_map[target.id] = PyIdent(
                            module=list([]), mb_name=Just(target.id)
                        )
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    env_map[node.target.id] = PyIdent(
                        module=list([]), mb_name=Just(node.target.id)
                    )
                self.generic_visit(node)

        Visitor().visit(tree)
        return IdEnv(env_map)


# Define the test class using pytest
class _TestIdEnv:
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
        id_env = IdEnv.from_file(source_code)

        assert id_env("os") == "os.os"
        assert id_env("namedtuple") == "collections.namedtuple"
        assert id_env("my_function") == ".my_function"
        assert id_env("MyClass") == ".MyClass"
        assert id_env("my_var") == ".my_var"
        assert id_env("other_var") == ".other_var"


@dataclass
class PyCode:
    ident: PyIdent
    code: Callable[[str], str]  # Assume that the file is already created
    deps: Map[str, PyDependecy]

    def strict_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )

    def weak_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(not d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )


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


def _all_idents_unique(codes: Iterable[PyCode]) -> bool:
    idents: Iterable[PyIdent] = map(lambda c: c.ident, codes)

    def is_unique(acc: bool, id: PyIdent) -> bool:
        return acc and (id not in idents)

    return foldl(is_unique, True, idents)


def _all_deps_present(codes: Iterable[PyCode]) -> bool:
    present_idents = concat(map(lambda c: c.deps.values(), codes))
    all_deps = unique(
        concat(map(lambda c: concat(map(lambda d: [d.ident], c.deps.values())), codes))
    )

    def _is_present(acc: bool, dep: PyDependecy) -> bool:
        res = elem(dep.ident, present_idents)
        if not res:
            raise ValueError(f"Dependency {dep.ident} is not present.")
        return acc and res

    return foldl(_is_present, True, all_deps)


def _no_strict_circular_deps(codes: Iterable[PyCode]) -> bool:
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


def are_valid_codes(codes: Iterable[PyCode]) -> bool:
    return (
        _all_idents_unique(codes)
        and _all_deps_present(codes)
        and _no_strict_circular_deps(codes)
    )


def _test_are_valid_codes():
    # Predefined (default) codes
    default_idents = [
        PyIdent(module=["os"], mb_name=Just("os")),
        PyIdent(module=["os"], mb_name=Just("path")),
        PyIdent(module=["os"], mb_name=Just("join")),
    ]
    default_codes = [
        PyCode(
            ident=default_idents[0],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
        PyCode(
            ident=default_idents[1],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
        PyCode(
            ident=default_idents[2],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
    ]

    # Custom codes
    custom_idents = [
        PyIdent(module=["my_module"], mb_name=Just("my_function")),
        PyIdent(module=["my_module"], mb_name=Just("MyClass")),
    ]
    custom_codes = [
        PyCode(
            ident=custom_idents[0],
            code=lambda _: "print('Hello World')",
            # deps={
            #     "os": PyDependecy(ident=default_idents[0], is_strict=True),
            #     "path": PyDependecy(ident=default_idents[1], is_strict=True),
            # },
            deps=Map(
                [
                    ("os", PyDependecy(ident=default_idents[0], is_strict=True)),
                    ("path", PyDependecy(ident=default_idents[1], is_strict=True)),
                ]
            ),
        ),
        PyCode(
            ident=custom_idents[1],
            code=lambda _: "class MyClass: pass",
            # deps={
            #     "join": PyDependecy(ident=default_idents[2], is_strict=True),
            # },
            deps=Map(
                [("join", PyDependecy(ident=default_idents[2], is_strict=True))],
            ),
        ),
    ]

    # Combine all codes
    codes = default_codes + custom_codes

    # Assertions to check validity
    assert _all_deps_present(codes)
    assert _all_idents_unique(codes)
    assert _no_strict_circular_deps(codes)
    assert are_valid_codes(codes)

    # Introduce a circular dependency to check for invalid codes
    custom_codes[0].deps["join"] = PyDependecy(ident=custom_idents[1], is_strict=True)
    assert not are_valid_codes(codes)

    # Fix the previous issue but introduce another circular dependency
    custom_codes[0].deps["join"] = PyDependecy(ident=default_idents[2], is_strict=True)
    custom_codes[1].deps["os"] = PyDependecy(ident=custom_idents[0], is_strict=True)
    assert not are_valid_codes(codes)

    # Correct the dependencies to be valid again
    custom_codes[1].deps["os"] = PyDependecy(ident=default_idents[0], is_strict=True)
    assert are_valid_codes(codes)


def raw_ordered_codes(codes: Iterable[PyCode]) -> Iterable[PyCode]:
    def maybe_free_code(sorted_codes: Iterable[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter(lambda c: c not in sorted_codes, codes)

        def is_free(code: PyCode) -> bool:
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            return all(map(lambda i: i.ident in sorted_ids, code.deps.values()))

        free_codes = filter(is_free, unsorted_codes)

        try:
            return Just(head(free_codes))
        except StopIteration:
            return Nothing()

    def maybe_loosely_free_code(sorted_codes: Iterable[PyCode]) -> Maybe[PyCode]:
        unsorted_codes = filter(lambda c: c not in sorted_codes, codes)

        def is_loosely_free(code: PyCode) -> bool:
            sorted_ids = map(lambda c: c.ident, sorted_codes)
            return all(map(lambda i: i in sorted_ids, code.strict_deps()))

        free_codes = filter(is_loosely_free, unsorted_codes)
        less_deps_first = sort_on(lambda c: length(c.weak_deps()), free_codes)

        try:
            return Just(head(less_deps_first))
        except StopIteration:
            return Nothing()

    def _order(acc: Iterable[PyCode], unordered: Iterable[PyCode]) -> Iterable[PyCode]:
        if unordered == []:
            return acc
        else:
            if mb_code := maybe_free_code(acc):
                return _order(concat([acc, [mb_code.unwrap()]]), unordered)
            elif mb_code := maybe_loosely_free_code(acc):
                return _order(concat([acc, [mb_code.unwrap()]]), unordered)
            else:
                # ! temp
                raise RuntimeError(f"Should be unreachable. acc: {acc}, unordered: {unordered}")
                raise RuntimeError("Should be unreachable")

    return _order([], codes)


def _test_raw_ordered_codes():
    # Predefined (default) codes
    default_idents = [
        PyIdent(module=["os"], mb_name=Just("os")),
        PyIdent(module=["os"], mb_name=Just("path")),
        PyIdent(module=["os"], mb_name=Just("join")),
    ]
    default_codes = [
        PyCode(
            ident=default_idents[0],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
        PyCode(
            ident=default_idents[1],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
        PyCode(
            ident=default_idents[2],
            code=lambda _: "",  # No actual implementation
            deps=Map(),
        ),
    ]

    # Custom codes
    custom_idents = [
        PyIdent(module=["my_module"], mb_name=Just("my_function")),
        PyIdent(module=["my_module"], mb_name=Just("MyClass")),
    ]
    custom_codes = [
        PyCode(
            ident=custom_idents[0],
            code=lambda _: "print('Hello World')",
            deps=Map(
                [
                    ("os", PyDependecy(ident=default_idents[0], is_strict=True)),
                    ("path", PyDependecy(ident=default_idents[1], is_strict=True)),
                ]
            ),
        ),
        PyCode(
            ident=custom_idents[1],
            code=lambda _: "class MyClass: pass",
            deps=Map(
                [("join", PyDependecy(ident=default_idents[2], is_strict=True))],
            ),
        ),
    ]

    # Combine all codes
    codes = default_codes + custom_codes

    # Order the codes
    ordered_codes = raw_ordered_codes(codes)

    # Check the order
    assert ordered_codes == custom_codes + default_codes