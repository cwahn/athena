from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from entoli.base.typeclass import Monad


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass(frozen=True, slots=True)
class Identity(Generic[_A], Monad[_A]):
    run: _A

    def fmap(self, f: Callable[[_A], _B]) -> "Identity[_B]":
        return Identity(f(self.run))

    @staticmethod
    def pure(x: _A) -> "Identity[_A]":
        return Identity(x)

    def ap(self, f: "Identity[Callable[[_A], _B]]") -> "Identity[_B]":
        return Identity(f.run(self.run))

    def and_then(self, f: Callable[[_A], "Identity[_B]"]) -> "Identity[_B]":
        return f(self.run)

    def then(self, x: "Identity[_B]") -> "Identity[_B]":
        return self.and_then(lambda _: x)
