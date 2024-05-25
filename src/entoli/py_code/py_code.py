import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Dict
from entoli.base.io import Io
from entoli.base.maybe import Just, Maybe, Nothing

from entoli.prelude import (
    append,
    body,
    concat_map,
    elem,
    for_each,
    lines,
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
    split_at,
    tail,
    unique,
    unlines,
)
from entoli.system import create_dir_if_missing, file_exists, read_file, write_file


@dataclass
class PyIdent:
    module: Iterable[str]
    mb_name: Maybe[str]

    def module_name(self) -> str:
        return ".".join(self.module)

    def rel_module_path(self) -> Path:
        file_name = last(self.module) + ".py"
        module_init = init(self.module)
        return Path(*module_init, file_name)

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

    def relative_name_to(self, other_parts: Iterable[str]) -> Maybe[str]:
        def _relative_name_to(
            self_part: Iterable[str], other_part: Iterable[str]
        ) -> Maybe[str]:
            match self_part:
                case []:
                    return Nothing()
                case [self_head, *self_tail]:
                    match other_part:
                        case []:
                            return Just(".".join(self_part))
                        case [other_head, *other_tail]:
                            if self_head != other_head:
                                return Just(".".join(self_part))
                            else:
                                return _relative_name_to(self_tail, other_tail)

            raise RuntimeError("Unreachable code")

        return _relative_name_to(self.full_qual_name_parts(), other_parts)

    def refered_as_in(self, id_env: "IdEnv") -> str:
        relevant_env = filter_map(
            # lambda key_name_parts: if_else(snd(key_name_parts).includes(self), Just(key_name_parts), Nothing()),
            # if relavent includes self
            lambda key_id: if_else(
                is_prefix_of(snd(key_id), self.full_qual_name_parts()),
                Just(key_id),
                Nothing(),
            ),
            id_env.inner.items(),
        )

        if length(relevant_env) == 0:
            raise ValueError(f"No relevant env for {self}, not defined or included.")
        elif length(relevant_env) > 1:
            raise ValueError(
                f"Multiple relevant env for {self}, {relevant_env}. Ambiguous."
            )
        else:
            # relevent_key = fst(head(relevant_env))
            # relevant_ident = snd(head(relevant_env))
            relevent_key, relevant_name_parts = head(relevant_env)

            if (
                self.full_qual_name_parts() == relevant_name_parts
            ):  # exact import or definition
                return relevent_key
            else:  # partial import
                return (
                    relevent_key
                    + "."
                    + self.relative_name_to(relevant_name_parts).unwrap()
                )

    def mb_import_line(self, id_env: "IdEnv") -> Maybe[str]:
        if self.module == []:  # In-file definition, no need to import
            return Nothing()
        else:
            mb_relevent = find(
                # lambda key_id: snd(key_id).includes(self), id_env.inner.items()
                lambda key_name_parts: is_prefix_of(
                    snd(key_name_parts), self.full_qual_name_parts()
                ),
                id_env.inner.items(),
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
                                f"from {'.'.join(init(self.module))} import {last_module_name}"
                            )
                        else:  # Conflict
                            return Just(
                                f"from {'.'.join(init(self.module))} import {last_module_name} as {last_module_name}_"
                            )
                else:  # Self is a name in a module
                    fully_qualified = self.full_qual_name_parts()
                    last_name = last(fully_qualified)
                    if last_name not in id_env.inner:
                        return Just(
                            f"from {'.'.join(init(fully_qualified))} import {last_name}"
                        )
                    else:
                        return Just(
                            f"from {'.'.join(init(fully_qualified))} import {last_name} as {last_name}_"
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

    def _test_PyIdent_relative_name_to(self):
        # Qualified names are not considered.
        # This is for module-level or upper.

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        other = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.relative_name_to(other.full_qual_name_parts()) == Just("os")

        ident = PyIdent(module=["os"], mb_name=Nothing())
        other = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.relative_name_to(other.full_qual_name_parts()) == Nothing()

        ident = PyIdent(module=["os"], mb_name=Nothing())
        other = PyIdent(module=["os", "path"], mb_name=Just("path"))
        assert ident.relative_name_to(other.full_qual_name_parts()) == Nothing()

        ident = PyIdent(module=["os", "path"], mb_name=Just("path"))
        other = PyIdent(module=["os"], mb_name=Nothing())
        assert ident.relative_name_to(other.full_qual_name_parts()) == Just("path.path")

        # ref_ident = PyIdent(module=["auto_project", "auto_app_0"], mb_name=Just("urls"))
        # ident = PyIdent(
        #     module=["auto_project", "auto_app_0", "urls"], mb_name=Nothing()
        # )
        # assert ident.relative_name_to(ref_ident) == Just("urls")

    def _test_PyIdent_inverse_id_env(self):
        id_env = IdEnv(
            # inner={
            #     "os": PyIdent(module=["os"], mb_name=Just("os")),
            #     "os.path": PyIdent(module=["os"], mb_name=Just("os.path")),
            #     "os.path.join": PyIdent(module=["os"], mb_name=Just("os.path.join")),
            # }
            inner={
                "os": ["os", "os"],
                "os.path": ["os", "os", "path"],
                "os.path.join": ["os", "os", "path", "join"],
            }
        )

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.refered_as_in(id_env) == "os"

        ident = PyIdent(module=["os"], mb_name=Just("os.path"))
        assert ident.refered_as_in(id_env) == "os.path"

        ident = PyIdent(module=["os"], mb_name=Just("os.path.join"))
        assert ident.refered_as_in(id_env) == "os.path.join"

    def _test_PyIdent_mb_import_line(self):
        name_env = IdEnv(
            # inner={
            #     "os": PyIdent(module=["os"], mb_name=Just("os")),
            #     "os.path": PyIdent(module=["os"], mb_name=Just("os.path")),
            #     "os.path.join": PyIdent(module=["os"], mb_name=Just("os.path.join")),
            # }
            inner={
                "os": ["os", "os"],
                "os.path": ["os", "os", "path"],
                "os.path.join": ["os", "os", "path", "join"],
            }
        )

        ident = PyIdent(module=["os"], mb_name=Just("os"))
        assert ident.mb_import_line(name_env) == Nothing()

        # todo Name of item the same with the module name need to be handled.

        # ! Qualified names are not considered. PyIdent is for module-level item of upper.

    def _test_PyIdent_mb_import_line(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))

        assert ident.mb_import_line(IdEnv({})) == Just("from os import os")


@dataclass
class PyDependecy:
    ident: PyIdent
    is_strict: bool = True


@dataclass
class IdEnv:
    inner: Dict[str, Iterable[str]]

    def __call__(self, name: str) -> str:
        len = length(self.inner[name])
        assert not isinstance(self.inner[name], str)
        if len == 0:
            raise ValueError(f"Name {name} is not defined in the environment.")
        elif len == 1:
            return head(self.inner[name])
        else:
            return ".".join(self.inner[name])

    @staticmethod
    def from_source(src: str) -> "IdEnv":
        if src == "":
            return IdEnv({})

        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in the source code: {e}, src: {src}")
        env_map = {}

        class Visitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    # module = alias.name
                    # env_map[alias.asname or alias.name] = PyIdent(
                    #     module=[module], mb_name=Just(alias.name)
                    # )
                    env_map[alias.asname or alias.name] = [alias.name]

            def visit_ImportFrom(self, node):
                match node.module:
                    case None:
                        module_parts = []
                    case md:
                        module_parts = md.split(".")

                # if "*" in [alias.name for alias in node.names]:
                #     env_map[node.module] = PyIdent(
                #         module=module_parts, mb_name=Just("*")
                #     )

                # else:
                for alias in node.names:
                    env_map[alias.asname or alias.name] = [alias.name]
                    # qual_name = alias.name
                    # env_map[alias.asname or alias.name] = PyIdent(
                    #     # ! This name could be either module or item in the module.
                    #     # ! There is no way to distinguish them.
                    #     module=module_parts,
                    #     mb_name=Just(qual_name),
                    # )

            def visit_FunctionDef(self, node):
                qual_name = node.name
                # env_map[qual_name] = PyIdent(module=[], mb_name=Just(qual_name))
                env_map[qual_name] = [qual_name]
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                qual_name = node.name
                # env_map[qual_name] = PyIdent(module=[], mb_name=Just(qual_name))
                env_map[qual_name] = [qual_name]
                self.generic_visit(node)

            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # env_map[target.id] = PyIdent(module=[], mb_name=Just(target.id))
                        env_map[target.id] = [target.id]
                self.generic_visit(node)

            def visit_AnnAssign(self, node):
                if isinstance(node.target, ast.Name):
                    # env_map[node.target.id] = PyIdent(
                    #     module=[], mb_name=Just(node.target.id)
                    # )
                    env_map[node.target.id] = [node.target.id]
                self.generic_visit(node)

        Visitor().visit(tree)
        return IdEnv(env_map)


# Define the test class using pytest
class _TestIdEnv:
    def _test_from_source(self):
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
        id_env = IdEnv.from_source(source_code)

        assert id_env("os") == "os"
        assert id_env("namedtuple") == "namedtuple"
        assert id_env("my_function") == "my_function"
        assert id_env("MyClass") == "MyClass"
        assert id_env("my_var") == "my_var"
        assert id_env("other_var") == "other_var"

    def _test_from_source_(self):
        source_code = ""
        ident = PyIdent(
            module=["auto_project", "auto_app_0", "urls"], mb_name=Nothing()
        )

        mb_import_line = ident.mb_import_line(IdEnv.from_source(source_code))
        source_code_ = mb_import_line.unwrap()

        imported_id_env = IdEnv.from_source(source_code_)
        assert ident.refered_as_in(imported_id_env) == ".urls"


# Take depencies keys and return python idendifiers in the code
ReferEnv = Callable[[str], str]


@dataclass
class PyCode:
    ident: PyIdent
    code: Callable[[ReferEnv, str], str]  # Assume that the file is already created
    deps: Dict[str, PyDependecy]

    def rel_module_path(self) -> Path:
        return self.ident.rel_module_path()

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

    def code_to_content(
        self, imported_content: str
    ) -> str:  # Assume all the dependencies are already imported
        id_env = IdEnv.from_source(imported_content)

        def _refer(dep_key: str) -> str:
            dep_ident = self.deps[dep_key].ident
            return dep_ident.refered_as_in(id_env)

        return self.code(_refer, imported_content)


class _TestPyCode:
    def test_strict_deps(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        deps = {
            "os": PyDependecy(ident=ident, is_strict=True),
            "path": PyDependecy(ident=ident, is_strict=False),
        }
        code = PyCode(ident=ident, code=lambda _, __: "", deps=deps)

        assert code.strict_deps() == [ident]

    def test_weak_deps(self):
        ident = PyIdent(module=["os"], mb_name=Just("os"))
        deps = {
            "os": PyDependecy(ident=ident, is_strict=True),
            "path": PyDependecy(ident=ident, is_strict=False),
        }
        code = PyCode(ident=ident, code=lambda _, __: "", deps=deps)

        assert code.weak_deps() == [ident]

    def test_code_to_content(self):
        # ident =
        deps = {
            "os": PyDependecy(
                ident=PyIdent(module=["os"], mb_name=Just("os")), is_strict=True
            ),
            "path": PyDependecy(
                ident=PyIdent(module=["os"], mb_name=Just("path")), is_strict=False
            ),
        }
        code = PyCode(
            ident=PyIdent(module=["."], mb_name=Nothing()),
            code=lambda refer, _: refer("os"),
            deps=deps,
        )

        assert code.code_to_content("import os") == "os.os"


def _append_import_lines(content: str, import_lines: Iterable[str]) -> str:
    lines_ = lines(content)
    # Find the end of the import statements
    import_end = 0
    for i, line in enumerate(lines_):
        if line.startswith("import ") or line.startswith("from "):
            import_end = i + 1
        elif line.strip() == "":
            continue
        else:
            break

    existing_import_lines, rest_lines = split_at(import_end, lines_)
    import_inserted_lines = concat([existing_import_lines, import_lines, rest_lines])

    return unlines(import_inserted_lines)


def _test_import_and_refer():
    # Import identifiers to a empty contents, and check if the imported identifiers are refered correctly.
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
    id_env = IdEnv.from_source(source_code)

    ident_to_import_0 = PyIdent(module=["os"], mb_name=Just("os"))
    ident_to_import_1 = PyIdent(module=["collections"], mb_name=Just("namedtuple"))
    ident_to_import_2 = PyIdent(module=[], mb_name=Just("my_function"))
    ident_to_import_3 = PyIdent(
        module=["auto_project", "auto_app_0", "urls"], mb_name=Nothing()
    )

    import_lines = filter_map(
        lambda ident: ident.mb_import_line(id_env),
        [ident_to_import_0, ident_to_import_1, ident_to_import_2, ident_to_import_3],
    )

    imported_content = _append_import_lines(source_code, import_lines)

    imported_id_env = IdEnv.from_source(imported_content)

    def _refer(ident: PyIdent) -> str:
        return ident.refered_as_in(imported_id_env)

    assert _refer(ident_to_import_0) == "os.os" # os module is imported as os. Therefore, it is refered as os.os
    assert _refer(ident_to_import_1) == "namedtuple"
    assert _refer(ident_to_import_2) == "my_function"
    print("imported_content: ", imported_content)
    print("imported_id_env: ", imported_id_env.inner)
    assert _refer(ident_to_import_3) == ".urls"


def _all_idents_unique(codes: Iterable[PyCode]) -> bool:
    idents: Iterable[PyIdent] = map(lambda c: c.ident, codes)

    def _inner(acc: Maybe[Iterable[PyIdent]], id: PyIdent) -> Maybe[Iterable[PyIdent]]:
        match acc:
            case Nothing():
                return Nothing()
            case Just(visited_idents):
                if id in visited_idents:
                    return Nothing()
                else:
                    return Just(concat([visited_idents, [id]]))

    res = foldl(_inner, Just([]), idents)

    if res == Nothing():
        return False
    else:
        return True


def _all_deps_present(codes: Iterable[PyCode]) -> bool:
    present_idents = map(lambda c: c.ident, codes)
    code_depss = map(lambda c: c.deps.values(), codes)
    all_deps = unique(concat(code_depss))

    def _is_present(acc: bool, dep: PyDependecy) -> bool:
        return acc and elem(dep.ident, present_idents)

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


def _are_valid_codes(codes: Iterable[PyCode]) -> bool:
    return (
        # _all_idents_unique(codes)
        # and
        _all_deps_present(codes) and _no_strict_circular_deps(codes)
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
            code=lambda _, __: "",  # No actual implementation
            deps={},
        ),
        PyCode(
            ident=default_idents[1],
            code=lambda _, __: "",  # No actual implementation
            deps={},
        ),
        PyCode(
            ident=default_idents[2],
            code=lambda _, __: "",  # No actual implementation
            deps={},
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
            code=lambda _, __: "print('Hello World')",
            deps={
                "os": PyDependecy(ident=default_idents[0], is_strict=True),
                "path": PyDependecy(ident=default_idents[1], is_strict=True),
            },
        ),
        PyCode(
            ident=custom_idents[1],
            code=lambda _, __: "class MyClass: pass",
            deps={
                "join": PyDependecy(ident=default_idents[2], is_strict=True),
                "my_function": PyDependecy(ident=custom_idents[0], is_strict=True),
            },
        ),
    ]

    # Combine all codes
    codes = default_codes + custom_codes

    # Assertions to check validity
    assert _all_deps_present(codes)
    assert _all_idents_unique(codes)
    assert _no_strict_circular_deps(codes)
    assert _are_valid_codes(codes)

    # Add missing dependency to custom codes
    missing_ident = PyIdent(module=["missing"], mb_name=Just("missing"))
    custom_codes[0].deps["missing"] = PyDependecy(ident=missing_ident, is_strict=True)
    assert not _all_deps_present(codes)
    assert _all_idents_unique(codes)
    assert _no_strict_circular_deps(codes)
    assert not _are_valid_codes(codes)

    # Remove the missing dependency
    del custom_codes[0].deps["missing"]
    # Add duplicated ident
    duplicated_codes = codes + custom_codes
    assert _all_deps_present(duplicated_codes)
    assert not _all_idents_unique(duplicated_codes)
    assert _no_strict_circular_deps(duplicated_codes)
    assert not _are_valid_codes(duplicated_codes)

    # Introduce a circular dependency to check for invalid codes
    custom_codes[0].deps["join"] = PyDependecy(ident=custom_idents[1], is_strict=True)
    assert _all_deps_present(codes)
    assert _all_idents_unique(codes)
    assert not _no_strict_circular_deps(codes)
    assert not _are_valid_codes(codes)


def _mb_free_code(
    unsorted_codes: Iterable[PyCode], sorted_codes: Iterable[PyCode]
) -> Maybe[PyCode]:
    def is_free(code: PyCode) -> bool:
        sorted_ids = map(lambda c: c.ident, sorted_codes)
        return all(map(lambda i: i.ident in sorted_ids, code.deps.values()))

    free_codes = filter(is_free, unsorted_codes)

    try:
        return Just(head(free_codes))
    except StopIteration:
        return Nothing()


def _mb_loosely_free_code(
    unsorted_codes: Iterable[PyCode], sorted_codes: Iterable[PyCode]
) -> Maybe[PyCode]:
    def is_loosely_free(code: PyCode) -> bool:
        sorted_ids = map(lambda c: c.ident, sorted_codes)
        return all(filter(lambda dep: dep.ident in sorted_ids, code.deps.values()))

    free_codes = filter(is_loosely_free, unsorted_codes)
    less_deps_first = sort_on(lambda c: length(c.deps), free_codes)

    try:
        return Just(head(less_deps_first))
    except StopIteration:
        return Nothing()


def _raw_ordered_codes(codes: Iterable[PyCode]) -> Iterable[PyCode]:
    def _raw_ordered_codes(
        acc: Iterable[PyCode], unordered: Iterable[PyCode]
    ) -> Iterable[PyCode]:
        if not unordered:  # Check if unordered is empty
            return acc
        else:
            free_code_result = _mb_free_code(unordered, acc)
            if isinstance(free_code_result, Just):
                free_code = free_code_result.value
                return _raw_ordered_codes(
                    append(acc, [free_code]),
                    filter(lambda c: c != free_code, unordered),
                )
            else:
                loosely_free_code_result = _mb_loosely_free_code(unordered, acc)
                if isinstance(loosely_free_code_result, Just):
                    loosely_free_code = loosely_free_code_result.value
                    return _raw_ordered_codes(
                        append(acc, [loosely_free_code]),
                        filter(lambda c: c != loosely_free_code, unordered),
                    )
                else:
                    raise RuntimeError("Should be unreachable")

    return _raw_ordered_codes([], list(codes))


def _test_raw_ordered_codes():
    default_idents = [
        PyIdent(module=["os"], mb_name=Just("os")),
        PyIdent(module=["os"], mb_name=Just("path")),
        PyIdent(module=["os"], mb_name=Just("join")),
    ]
    default_codes = [
        PyCode(
            ident=default_idents[0],
            code=lambda _, __: "",  # No actual implementation
            deps={},
        ),
        PyCode(
            ident=default_idents[1],
            code=lambda _, __: "",  # No actual implementation
            deps={},
        ),
        PyCode(
            ident=default_idents[2],
            code=lambda _, __: "",  # No actual implementation
            deps={},
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
            code=lambda _, __: "print('Hello World')",
            deps={
                "os": PyDependecy(ident=default_idents[0], is_strict=True),
                "path": PyDependecy(ident=default_idents[1], is_strict=True),
            },
        ),
        PyCode(
            ident=custom_idents[1],
            code=lambda _, __: "class MyClass: pass",
            deps={
                "join": PyDependecy(ident=default_idents[2], is_strict=True),
            },
        ),
    ]

    # Combine all codes
    codes = custom_codes + default_codes

    assert _raw_ordered_codes(codes) == [
        default_codes[0],
        default_codes[1],
        custom_codes[0],
        default_codes[2],
        custom_codes[1],
    ]

    custom_codes[0].deps["join"] = PyDependecy(ident=default_idents[2], is_strict=True)

    assert _raw_ordered_codes(codes) == [
        default_codes[0],
        default_codes[1],
        default_codes[2],
        custom_codes[0],
        custom_codes[1],
    ]

    # assert False


def mb_ordered_codes(codes: Iterable[PyCode]) -> Maybe[Iterable[PyCode]]:
    if _are_valid_codes(codes):
        return Just(_raw_ordered_codes(codes))
    else:
        return Nothing()


def amended_content(content: str, code: PyCode) -> str:
    id_env = IdEnv.from_source(content)

    dep_idents = map(lambda dep: dep.ident, code.deps.values())
    import_lines = filter_map(lambda ident: ident.mb_import_line(id_env), dep_idents)

    imported_content = _append_import_lines(content, import_lines)

    return code.code_to_content(imported_content)


def write_code(dir_path: Path, code: PyCode) -> Io[None]:
    file_path = dir_path / code.ident.rel_module_path()

    return (
        file_exists(file_path)
        .and_then(
            lambda exists: if_else(
                exists,
                Io.pure(None),
                create_dir_if_missing(True, file_path.parent).then(
                    write_file(file_path, "")
                ),
            )
        )
        .then(
            read_file(file_path).and_then(
                lambda content: write_file(file_path, amended_content(content, code))
            )
        )
    )


def write_codes(dir_path: Path, codes: Iterable[PyCode]) -> Io[None]:
    match mb_ordered_codes(codes):
        case Nothing():
            # if not _all_idents_unique(codes):
            #     idents: Iterable[PyIdent] = map(lambda c: c.ident, codes)

            #     for_each(
            #         lambda ident: body(
            #             degeneracy := length(filter(lambda i: i == ident, idents)),
            #             if_else(
            #                 degeneracy > 1,
            #                 print(
            #                     f"Duplicated ident: {ident}, degeneracy: {degeneracy}"
            #                 ),
            #                 None,
            #             ),
            #         ),
            #         idents,
            #     )

            #     raise ValueError("Idents are not unique")
            # el

            if not _all_deps_present(codes):
                deps = unique(concat_map(lambda c: c.deps.values(), codes))
                for dep in deps:
                    if not elem(dep.ident, map(lambda c: c.ident, codes)):
                        print(f"Dependency not present: {dep.ident}")

                raise ValueError("Some dependencies are not present")
            elif not _no_strict_circular_deps(codes):
                raise ValueError("Codes are not valid")

            raise ValueError("Codes are not valid")
        case Just(ordered_codes):
            return foldl(
                lambda io, code: io.then(write_code(dir_path, code)),
                Io.pure(None),
                ordered_codes,
            )
