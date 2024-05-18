from __future__ import annotations
from typing import Any, Callable, Generic, Protocol, TypeVar
from dataclasses import dataclass


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


# Fuctor_co = TypeVar("Fuctor_co", bound="Functor", covariant=True)
# Functor_A = "Functor[A]"
# Functor_B = "Functor[B]"

# F = TypeVar("F")
# Fuctor_ = TypeVar("Fuctor_", bound="Functor", covariant=True,)


class Functor(Protocol[_A_co]):
    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A]) -> Any[_B]: ...


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    @staticmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Any[_B]: ...


class Monad(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Any[_B]: ...


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


class Random(Generic[_A]):
    pass


def taking_monad(x: Monad[int]) -> bool:
    return True

Io.fmap(lambda x: x + 1, Io(lambda: 1))

taking_monad(Io(lambda: 1))
# taking_monad(Random())


def taking_fuctor(x: Functor[int]) -> bool:
    return True


taking_fuctor(Io(lambda: 1))
