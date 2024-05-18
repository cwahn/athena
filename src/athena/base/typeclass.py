from __future__ import annotations
from typing import Any, Callable, Protocol, Type, TypeVar, runtime_checkable

from more_itertools import take


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Functor(Protocol[_A_co]):
    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A_co]) -> Any[_B]: ...


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    @staticmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Any[_B]: ...


class Monad(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Any[_B]: ...


# Monkey-patch implementations


@runtime_checkable
class DuckLike(Protocol):
    def quack(self) -> None: ...


class Dog:
    def bark(self) -> None:
        print("Woof")


def impl_duck(cls: Type) -> None:
    cls.quack = lambda self: print("Quack")


def add_protocol(cls: Type) -> Type:
    impl_duck(cls)
    return type(cls.__name__, (cls, DuckLike), {})


def quack(duck: DuckLike) -> None:
    duck.quack()


# Does raise an error
# take_duck(Dog())

Dog = add_protocol(Dog)

quack(Dog())
