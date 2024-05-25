from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Generic, Protocol, TypeVar

from .typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


# class _Maybe(Monad[_A], Protocol[_A]):
#     @staticmethod
#     def fmap(f: Callable[[_A], _B], x: _Maybe[_A]) -> _Maybe[_B]: ...

#     @staticmethod
#     def pure(x: _A) -> _Maybe[_A]: ...

#     @staticmethod
#     def ap(f: _Maybe[Callable[[_A], _B]], x: _Maybe[_A]) -> _Maybe[_B]: ...

#     @staticmethod
#     def bind(x: _Maybe[_A], f: Callable[[_A], _Maybe[_B]]) -> _Maybe[_B]: ...

#     def map(self, f: Callable[[_A], _B]) -> _Maybe[_B]: ...

#     def and_then(self, f: Callable[[_A], _Maybe[_B]]) -> _Maybe[_B]: ...

#     def then(self, x: _Maybe[_B]) -> _Maybe[_B]: ...

#     def unwrap(self) -> _A: ...

#     def unwrap_or(self, default: _A) -> _A: ...


@dataclass
# class Just(_Maybe[_A]):
class Just(Generic[_A]):
    value: _A

    def __repr__(self) -> str:
        return f"Just({self.value})"

    def __str__(self) -> str:
        return self.__repr__()

    def __bool__(self) -> bool:
        return True

    # def __repr__(self) -> str:
    #     return f"Just {self.value}"

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Just[_A]) -> Maybe[_B]:
        return Just(f(x.value))

    @staticmethod
    def pure(x: _A) -> Maybe[_A]:
        return Just(x)

    @staticmethod
    def ap(f: Just[Callable[[_A], _B]], x: Just[_A]) -> Maybe[_B]:
        return Just(f.value(x.value))

    @staticmethod
    def bind(x: Just[_A], f: Callable[[_A], Just[_B]]) -> Maybe[_B]:
        return f(x.value)

    def map(self, f: Callable[[_A], _B]) -> Maybe[_B]:
        return Just(f(self.value))

    def and_then(self, f: Callable[[_A], Just[_B]]) -> Maybe[_B]:
        return f(self.value)

    def then(self, x: Just[_B]) -> Maybe[_B]:
        return x

    def unwrap(self) -> _A:
        return self.value

    def unwrap_or(self, default: _A) -> _A:
        return self.value


# class Nothing(_Maybe):
@dataclass
class Nothing:
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

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Nothing) -> Maybe[_B]:
        return Nothing()

    @staticmethod
    def pure(x: _A) -> Maybe[_A]:
        return Nothing()

    @staticmethod
    def ap(f: Nothing, x: Nothing) -> Maybe[Any]:
        return Nothing()

    @staticmethod
    def bind(x: Nothing, f: Callable[[_A], Nothing]) -> Maybe[_A]:
        return Nothing()

    def map(self, f: Callable[[_A], _B]) -> Maybe[_B]:
        return Nothing()

    def and_then(self, f: Callable[[_A], Maybe[_B]]) -> Nothing:
        return Nothing()

    def then(self, x: Nothing) -> Maybe[Any]:
        return Nothing()

    def unwrap(self) -> Any:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")

    def unwrap_or(self, default: _A) -> _A:
        return default


Maybe = Just[_A] | Nothing


maybe_42 = Just(42)
maybe_42_ = Nothing()

# if __name__ == "__main__":
#     if maybe_42:
#         print(maybe_42.unwrap())
#     else:
#         print("Nothing")

#     if maybe_42_:
#         print(maybe_42_.unwrap())
#     else:
#         print("Nothing")

#     maybe_21 = maybe_42.map(lambda x: x // 2)

#     def _maybe_int(x: int) -> Maybe[int]:
#         return Just(x)

#     maybe_int = _maybe_int(42)

#     maybe_21 = maybe_int.map(lambda x: x // 2)
