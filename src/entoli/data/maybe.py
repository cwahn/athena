from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from ..base.typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")

type Maybe[_A] = Just[_A] | Nothing


class _Maybe(Monad[_A], Protocol[_A]):
    ...
    # def fmap(self, f: Callable[[_A], _B]) -> _Maybe[_B]: ...


@dataclass(frozen=True, slots=True)
class Just(Generic[_A], _Maybe[_A]):
    value: _A

    def __repr__(self) -> str:
        return f"Just({self.value})"

    def __str__(self) -> str:
        return self.__repr__()

    def __bool__(self) -> bool:
        return True

    def fmap(self, f: Callable[[_A], _B]) -> Maybe[_B]:
        return Just(f(self.value))

    @staticmethod
    def pure(x: _A) -> Maybe[_A]:
        return Just(x)

    def ap(self, f: Just[Callable[[_A], _B]]) -> Maybe[_B]:
        return Just(f.value(self.value))

    def and_then(self, f: Callable[[_A], Maybe[_B]]) -> Maybe[_B]:
        return f(self.value)

    def then(self, x: Maybe[_B]) -> Maybe[_B]:
        return self.and_then(lambda _: x)

    def unwrap(self) -> _A:
        return self.value

    def unwrap_or(self, default: _A) -> _A:
        return self.value


# class Nothing(_Maybe):
@dataclass(frozen=True, slots=True)
class Nothing(_Maybe[_A]):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Nothing, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return "Nothing"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    def fmap(self, f: Callable[[_A], _B]) -> Maybe[_B]:
        return Nothing()

    @staticmethod
    def pure(x: _A) -> Maybe[_A]:
        return Nothing()

    def ap(self, f: Nothing) -> Maybe[_A]:
        return Nothing()

    def and_then(self, f: Callable[[_A], Maybe[_B]]) -> Maybe[_A]:
        return Nothing()

    def then(self, x: Nothing) -> Maybe[_A]:
        return Nothing()

    def unwrap(self) -> Any:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")

    def unwrap_or(self, default: _A) -> _A:
        return default
