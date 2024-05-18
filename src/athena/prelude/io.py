from __future__ import annotations
from typing import Any, Callable, Generic, Protocol, TypeVar
from dataclasses import dataclass
from typing import reveal_type


A = TypeVar("A")
B = TypeVar("B")

A_co = TypeVar("A_co", covariant=True)
B_co = TypeVar("B_co", covariant=True)


# Fuctor_co = TypeVar("Fuctor_co", bound="Functor", covariant=True)
Functor_A = "Functor[A]"
Functor_B = "Functor[B]"

F = TypeVar("F")
# Fuctor_ = TypeVar("Fuctor_", bound="Functor", covariant=True,)


class Functor(Protocol[A_co]):
    @staticmethod
    def fmap(f: Callable[[A], B], x: Any[A]) -> Any[B]: ...


class Applicative(Functor[A_co], Protocol[A_co]):
    @staticmethod
    def pure(x: Any) -> Any[A]: ...

    @staticmethod
    def ap(f: Any[Callable[[A], B]], x: Any[A]) -> Any[B]: ...


class Monad(Applicative[A_co], Protocol[A_co]):
    @staticmethod
    def bind(x: Any[A], f: Callable[[A], Any[B]]) -> Any[B]: ...


@dataclass
class Io(Generic[A]):
    action: Callable[[], A]

    @staticmethod
    def fmap(f: Callable[[A], B], x: Io[A]) -> Io[B]:
        return Io(lambda: f(x.action()))

    @staticmethod
    def pure(x: A) -> Io[A]:
        return Io(lambda: x)

    @staticmethod
    def ap(f: Io[Callable[[A], B]], x: Io[A]) -> Io[B]:
        return Io(lambda: f.action()(x.action()))

    @staticmethod
    def bind(x: Io[A], f: Callable[[A], Io[B]]) -> Io[B]:
        return Io(lambda: f(x.action()).action())

class Random(Generic[A]):
    pass

def taking_monad(x: Monad[int]) -> bool:
    return True


taking_monad(Io(lambda: 1))
taking_monad(Random())


def taking_fuctor(x: Functor[int]) -> bool:
    return True


taking_fuctor(Io(lambda: 1))
