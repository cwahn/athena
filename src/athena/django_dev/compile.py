# Compilation takes dependency graph and generates a Io

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List

from athena.base.io import Io
from athena.base.maybe import Just, Maybe, Nothing
from athena.prelude import concat, foldl, sort_on, map, filter, head


@dataclass
class PyIdent:
    module: List[str]
    qual_name: List[str]

    def re_file_path(self) -> Path:
        return Path(*self.module) / Path(*self.qual_name) / Path("__init__.py")

    def fulley_qualified_name(self) -> str:
        return ".".join(self.module + self.qual_name)

    def import_statement(self) -> str:
        return f"from {self.fulley_qualified_name()} import {self.qual_name[-1]}"


# 지정되어야 하는 dependency 는 code의 종류마다 다르다.
# 이걸 자동으로 지정해주기는 어렵다.

# # This could be seen as a node of a graph
# @dataclass
# class PyCode:
#     ident: PyIdent
#     code: List[str]


# # SomeParams ... -> PyCode


# # This could be seen as a edge of graphs
# def derive_some_codes(dep_ident0: PyIdent, dep_ident1: PyIdent) -> List[PyCode]: ...


# def write_py_code(py_code: PyCode) -> Io[None]: ...

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
