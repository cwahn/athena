from __future__ import annotations
from typing import Protocol, Self, TypeVar

from entoli.data.monad import Monad

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)

_A = TypeVar("_A")
_B = TypeVar("_B")


class MonadPlus(Monad[_A_co], Protocol[_A_co]):
    @staticmethod
    def mzero() -> MonadPlus[_A_co]: ...

    def mplus(self, other: Self) -> Self: ...
