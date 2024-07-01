from __future__ import annotations
from typing import Any, Callable, Protocol, TypeVar

from entoli.data.applicative import Applicative


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Monad(Applicative[_A_co], Protocol[_A_co]):
    # m a -> (a -> m b) -> m b
    def and_then(self, f: Callable[[_A], Any[_B]]) -> Monad[Any]: ...

    # ! Can't express with current type system
    # def then(self, x: Any[_B]) -> Monad[_B]:
    #     return self.and_then(lambda _: x)
