from __future__ import annotations
from typing import Callable, Generic, Optional, TypeVar
from dataclasses import dataclass

from .typeclass import Functor, Monad


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass
class Io(Generic[_A]):
    action: Callable[[], _A]

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Io[_A]) -> Io[_B]:
        return Io(lambda: f(x.action()))

    @staticmethod
    def pure(x: _A) -> Io[_A]:
        return Io(lambda: x)

    @staticmethod
    def ap(f: Io[Callable[[_A], _B]], x: Io[_A]) -> Io[_B]:
        return Io(lambda: f.action()(x.action()))

    @staticmethod
    def bind(x: Io[_A], f: Callable[[_A], Io[_B]]) -> Io[_B]:
        return Io(lambda: f(x.action()).action())

    def map(self, f: Callable[[_A], _B]) -> Io[_B]:
        return Io(lambda: f(self.action()))

    def and_then(self, f: Callable[[_A], Io[_B]]) -> Io[_B]:
        return Io(lambda: f(self.action()).action())

    def then(self, x: Io[_B]) -> Io[_B]:
        def inner() -> _B:
            self.action()
            return x.action()

        return Io(inner)
