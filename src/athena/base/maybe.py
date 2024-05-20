from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol, TypeVar

from typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


class _Maybe(Monad[_A], Protocol[_A]):
    @staticmethod
    # @abstractmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A]) -> _Maybe[_B]: ...

    @staticmethod
    # @abstractmethod
    def pure(x: _A) -> _Maybe[_A]: ...

    @staticmethod
    # @abstractmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> _Maybe[_B]: ...

    @staticmethod
    # @abstractmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> _Maybe[_B]: ...

    # @abstractmethod
    def map(self, f: Callable[[_A], _B]) -> _Maybe[_B]: ...

    # @abstractmethod
    def and_then(self, f: Callable[[_A], Any[_B]]) -> _Maybe[_B]: ...

    # @abstractmethod
    def then(self, x: Any[_B]) -> _Maybe[_B]: ...

    # @abstractmethod
    def unwrap(self) -> _A: ...


class Just(_Maybe[_A]):
    def __init__(self, value: _A):
        self.value = value

    def __repr__(self) -> str:
        return f"Just {self.value}"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return True

    # def __repr__(self) -> str:
    #     return f"Just {self.value}"

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Just[_A]) -> _Maybe[_B]:
        return Just(f(x.value))

    @staticmethod
    def pure(x: _A) -> _Maybe[_A]:
        return Just(x)

    @staticmethod
    def ap(f: Just[Callable[[_A], _B]], x: Just[_A]) -> _Maybe[_B]:
        return Just(f.value(x.value))

    @staticmethod
    def bind(x: Just[_A], f: Callable[[_A], Just[_B]]) -> _Maybe[_B]:
        return f(x.value)

    def map(self, f: Callable[[_A], _B]) -> _Maybe[_B]:
        return Just(f(self.value))

    def and_then(self, f: Callable[[_A], Just[_B]]) -> _Maybe[_B]:
        return f(self.value)

    def then(self, x: Just[_B]) -> _Maybe[_B]:
        return x

    def unwrap(self) -> _A:
        return self.value


class Nothing(_Maybe[Any]):
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return "Nothing"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Nothing) -> _Maybe[Any]:
        return Nothing()

    @staticmethod
    def pure(x: _A) -> _Maybe[Any]:
        return Nothing()

    @staticmethod
    def ap(f: Nothing, x: Nothing) -> _Maybe[Any]:
        return Nothing()

    @staticmethod
    def bind(x: Nothing, f: Callable[[_A], Nothing]) -> _Maybe[Any]:
        return Nothing()

    def map(self, f: Callable[[_A], _B]) -> _Maybe[Any]:
        return Nothing()

    def and_then(self, f: Callable[[_A], Nothing]) -> _Maybe[Any]:
        return Nothing()

    def then(self, x: Nothing) -> _Maybe[Any]:
        return Nothing()

    def unwrap(self) -> Any:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")
    

Maybe = Just[_A] | Nothing


maybe_42 = Just(42)
maybe_42_ = Nothing()

if __name__ == "__main__":
    if maybe_42:
        print(maybe_42.unwrap())
    else:
        print("Nothing")

    if maybe_42_:
        print(maybe_42_.unwrap())
    else:
        print("Nothing")

    maybe_21 = maybe_42.map(lambda x: x // 2)

    def _maybe_int(x: int) -> _Maybe[int]:
        return Just(x)

    maybe_int = _maybe_int(42)

    maybe_21 = maybe_int.map(lambda x: x // 2)
