from dataclasses import dataclass
from typing import Callable, Iterable, Dict

from pytest import Item

from entoli.base.maybe import Just, Nothing, Maybe
from entoli.map import Map
from entoli.prelude import filter_map, if_else


@dataclass
class PyIdent:
    module: Iterable[str]
    qual_name: Iterable[str]


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
    deps: Map[str, PyDependecy]

    def strict_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(d.is_strict, Just(d.ident), Nothing()), self.deps.values()
        )

    def weak_deps(self) -> Iterable[PyIdent]:
        return filter_map(
            lambda d: if_else(not d.is_strict, Just(d.ident), Nothing()),
            self.deps.values(),
        )
