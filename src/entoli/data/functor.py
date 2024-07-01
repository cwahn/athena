from __future__ import annotations
from typing import Any, Callable, Iterable, List, Protocol, Self, Type, TypeVar


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Functor(Protocol[_A_co]):
    # fmap :: Functor f => (a -> b) -> f a -> f b
    def fmap(self, f: Callable[[_A], _B]) -> Functor[_B]: ...
