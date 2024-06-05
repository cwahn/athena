from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from entoli.base.typeclass import Monad


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass
class Identity(Generic[_A], Monad[_A]):
    run: _A

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: "Identity[_A]") -> "Identity[_B]":
        return Identity(f(x.run))

    @staticmethod
    def pure(x: _A) -> "Identity[_A]":
        return Identity(x)

    @staticmethod
    def ap(f: "Identity[Callable[[_A], _B]]", x: "Identity[_A]") -> "Identity[_B]":
        return Identity(f.run(x.run))

    @staticmethod
    def bind(x: "Identity[_A]", f: Callable[[_A], "Identity[_B]"]) -> "Identity[_B]":
        return f(x.run)
