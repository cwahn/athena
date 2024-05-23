from dataclasses import dataclass
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


DepEnv = Callable[[str], str]


@dataclass
class PyCode:
    ident: PyIdent
    code: Callable[[str, DepEnv], str]  # Assume that the file is already created
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
