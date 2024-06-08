from __future__ import annotations
from typing import Callable, Generic, Optional, TypeVar
from dataclasses import dataclass

from .typeclass import Functor, Monad


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass(frozen=True, slots=True)
class Io(Generic[_A], Monad[_A]):
    action: Callable[[], _A]

    def fmap(self, f: Callable[[_A], _B]) -> Io[_B]:
        return Io(lambda: f(self.action()))

    @staticmethod
    def pure(x: _A) -> Io[_A]:
        return Io(lambda: x)

    def ap(self, f: Io[Callable[[_A], _B]]) -> Io[_B]:
        return Io(lambda: f.action()(self.action()))

    def and_then(self, f: Callable[[_A], Io[_B]]) -> Io[_B]:
        return Io(lambda: f(self.action()).action())

    def then(self, x: Io[_B]) -> Io[_B]:
        return self.and_then(lambda _: x)
