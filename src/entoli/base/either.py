from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from .typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


# class _Ei(Monad[_A], Protocol[_A]):
#     @staticmethod
#     def fmap(f: Callable[[_A], _B], x: _Ei[_A]) -> _Ei[_B]: ...

#     @staticmethod
#     def pure(x: _A) -> _Ei[_A]: ...

#     @staticmethod
#     def ap(f: _Ei[Callable[[_A], _B]], x: _Ei[_A]) -> _Ei[_B]: ...

#     @staticmethod
#     def bind(x: _Ei[_A], f: Callable[[_A], _Ei[_B]]) -> _Ei[_B]: ...

#     def map(self, f: Callable[[_A], _B]) -> _Ei[_B]: ...

#     def and_then(self, f: Callable[[_A], _Ei[_B]]) -> _Ei[_B]: ...

#     def then(self, x: _Ei[_B]) -> _Ei[_B]: ...

#     def unwrap(self) -> _A: ...

#     def unwrap_or(self, default: _A) -> _A: ...


@dataclass
class Left(Generic[_A]):
    value: _A

    def __repr__(self) -> str:
        return f"Left({self.value})"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Left) -> Ei[_B]:
        return Left()

    @staticmethod
    def pure(x: _A) -> Ei[_A]:
        return Left()

    @staticmethod
    def ap(f: Left, x: Left) -> Ei[Any]:
        return Left()

    @staticmethod
    def bind(x: Left, f: Callable[[_A], Left]) -> Ei[_A]:
        return Left()

    def map(self, f: Callable[[_A], _B]) -> Ei[_B]:
        return Left()

    def and_then(self, f: Callable[[_A], Ei[_B]]) -> Left:
        return Left()

    def then(self, x: Left) -> Ei[Any]:
        return Left()

    def unwrap(self) -> Any:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")

    def unwrap_or(self, default: _A) -> _A:
        return default


@dataclass
# class Right(_Ei[_A]):
class Right(Generic[_A]):
    value: _A

    def __repr__(self) -> str:
        return f"Right({self.value})"

    def __str__(self) -> str:
        return self.__repr__()

    def __bool__(self) -> bool:
        return True

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Right[_A]) -> Ei[_B]:
        return Right(f(x.value))

    @staticmethod
    def pure(x: _A) -> Ei[_A]:
        return Right(x)

    @staticmethod
    def ap(f: Right[Callable[[_A], _B]], x: Right[_A]) -> Ei[_B]:
        return Right(f.value(x.value))

    @staticmethod
    def bind(x: Right[_A], f: Callable[[_A], Right[_B]]) -> Ei[_B]:
        return f(x.value)

    def map(self, f: Callable[[_A], _B]) -> Ei[_B]:
        return Right(f(self.value))

    def and_then(self, f: Callable[[_A], Right[_B]]) -> Ei[_B]:
        return f(self.value)

    def then(self, x: Right[_B]) -> Ei[_B]:
        return x

    def unwrap(self) -> _A:
        return self.value

    def unwrap_or(self, default: _A) -> _A:
        return self.value


Either = Left[_A] | Right[_B]
