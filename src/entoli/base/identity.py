from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from entoli.base.typeclass import Monad


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass(frozen=True, slots=True)
class Identity(Generic[_A], Monad[_A]):
    run: _A

    # @staticmethod
    # def fmap(f: Callable[[_A], _B], x: "Identity[_A]") -> "Identity[_B]":
    #     return Identity(f(x.run))

    def fmap(self, f: Callable[[_A], _B]) -> "Identity[_B]":
        return Identity(f(self.run))

    @staticmethod
    def pure(x: _A) -> "Identity[_A]":
        return Identity(x)

    # @staticmethod
    # def ap(f: "Identity[Callable[[_A], _B]]", x: "Identity[_A]") -> "Identity[_B]":
    #     return Identity(f.run(x.run))

    def ap(self, f: "Identity[Callable[[_A], _B]]") -> "Identity[_B]":
        return Identity(f.run(self.run))

    # @staticmethod
    # def bind(x: "Identity[_A]", f: Callable[[_A], "Identity[_B]"]) -> "Identity[_B]":
    #     return f(x.run)

    def and_then(self, f: Callable[[_A], "Identity[_B]"]) -> "Identity[_B]":
        return f(self.run)
