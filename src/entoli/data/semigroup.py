from __future__ import annotations
from typing import Protocol, Self, TypeVar

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)

_A = TypeVar("_A")
_B = TypeVar("_B")


class Semigroup(Protocol[_A_co]):
    def op(self, other: Self) -> Self: ...
