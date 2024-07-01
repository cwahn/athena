from __future__ import annotations
from re import M
from typing import Any, Callable, Iterable, List, Protocol, Self, Type, TypeVar

from entoli.data.functor import Functor


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    # ap :: Applicative f => f (a -> b) -> f a -> f b
    def ap(self, f: Any[Callable[[_A_co], Any]]) -> Applicative[Any]: ...
