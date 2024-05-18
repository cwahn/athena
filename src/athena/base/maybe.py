from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar

from typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


class Maybe(Monad[_A], ABC):
    @staticmethod
    @abstractmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A]) -> Maybe[_B]: ...

    @staticmethod
    @abstractmethod
    def pure(x: _A) -> Maybe[_A]: ...

    @staticmethod
    @abstractmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Maybe[_B]: ...

    @staticmethod
    @abstractmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Maybe[_B]: ...

    @abstractmethod
    def map(self, f: Callable[[_A], _B]) -> Maybe[_B]: ...

    @abstractmethod
    def and_then(self, f: Callable[[_A], Any[_B]]) -> Maybe[_B]: ...

    @abstractmethod
    def then(self, x: Any[_B]) -> Maybe[_B]: ...

    @abstractmethod
    def unwrap(self) -> _A: ...


class Just(Maybe[_A]):
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


class Nothing(Maybe[Any]):
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return "Nothing"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Nothing) -> Maybe[Any]:
        return Nothing()

    @staticmethod
    def pure(x: _A) -> Maybe[Any]:
        return Nothing()

    @staticmethod
    def ap(f: Nothing, x: Nothing) -> Maybe[Any]:
        return Nothing()

    @staticmethod
    def bind(x: Nothing, f: Callable[[_A], Nothing]) -> Maybe[Any]:
        return Nothing()

    def map(self, f: Callable[[_A], _B]) -> Maybe[Any]:
        return Nothing()

    def and_then(self, f: Callable[[_A], Nothing]) -> Maybe[Any]:
        return Nothing()

    def then(self, x: Nothing) -> Maybe[Any]:
        return Nothing()

    def unwrap(self) -> None:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")


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

    def _maybe_int(x: int) -> Maybe[int]:
        return Just(x)

    maybe_int = _maybe_int(42)

    maybe_21 = maybe_int.map(lambda x: x // 2)
