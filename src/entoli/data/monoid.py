from __future__ import annotations
from typing import Callable, Iterable, Protocol, Self, Type, TypeVar
from entoli._base.typeclass import Functor, Monad
from entoli.data.semigroup import Semigroup

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)

_A = TypeVar("_A")
_B = TypeVar("_B")


class MonoidBase(Semigroup, Protocol):  # Required methods for Monoid
    @staticmethod
    def mempty() -> Monoid:
        raise NotImplementedError


class Monoid(MonoidBase, Protocol):  # Default implementation of Monoid
    def mappend(self, other: Self) -> Self:
        return self.op(other)

    @staticmethod
    def mconcat(xs: Iterable) -> Monoid:
        from entoli.prelude import foldr

        return foldr(lambda x, acc: x.op(acc), Monoid.mempty(), xs)  # type: ignore
