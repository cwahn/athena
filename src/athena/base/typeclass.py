from __future__ import annotations
from typing import Any, Callable, Protocol, TypeVar


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Functor(Protocol[_A_co]):
    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A_co]) -> Any[_B]: ...


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    @staticmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Any[_B]: ...


class Monad(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Any[_B]: ...
