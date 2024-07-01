from __future__ import annotations
from typing import Callable, Protocol, Self, Type, TypeVar
from entoli._base.typeclass import Functor, Monad

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)

_A = TypeVar("_A")
_B = TypeVar("_B")


class MonadPlus(Monad[_A_co], Protocol[_A_co]):
    @staticmethod
    def mzero() -> MonadPlus[_A_co]: ...

    def mplus(self, other: Self) -> Self: ...


class Foldable(Protocol[_A_co]):
    def foldr(self, f: Callable[[_A_co, _B], _B], z: _B) -> _B: ...

    def foldl(self, f: Callable[[_B, _A_co], _B], z: _B) -> _B: ...

    def fold_map(self, f: Callable[[_A_co], _B], z: Type[_B]) -> _B: ...


class Traversable(Functor[_A_co], Foldable[_A_co], Protocol[_A_co]):
    def traverse(self, f: Callable[[_A_co], _B], t: Type[_B]) -> _B: ...

    def sequence(self, t: Type[_A_co]) -> _A_co: ...
