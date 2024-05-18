from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar

from typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


class Result(Monad[_A], ABC):
    @staticmethod
    @abstractmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A]) -> Result[_B]: ...

    @staticmethod
    @abstractmethod
    def pure(x: _A) -> Result[_A]: ...

    @staticmethod
    @abstractmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Result[_B]: ...

    @staticmethod
    @abstractmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Result[_B]: ...

    @abstractmethod
    def map(self, f: Callable[[_A], _B]) -> Result[_B]: ...

    @abstractmethod
    def and_then(self, f: Callable[[_A], Any[_B]]) -> Result[_B]: ...

    @abstractmethod
    def then(self, x: Any[_B]) -> Result[_B]: ...

    @abstractmethod
    def unwrap(self) -> _A: ...


class Ok(Result[_A]):
    def __init__(self, value: _A):
        self.value = value

    def __repr__(self) -> str:
        return f"Ok {self.value}"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return True

    # def __repr__(self) -> str:
    #     return f"Ok {self.value}"

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Ok[_A]) -> Result[_B]:
        return Ok(f(x.value))

    @staticmethod
    def pure(x: _A) -> Result[_A]:
        return Ok(x)

    @staticmethod
    def ap(f: Ok[Callable[[_A], _B]], x: Ok[_A]) -> Result[_B]:
        return Ok(f.value(x.value))

    @staticmethod
    def bind(x: Ok[_A], f: Callable[[_A], Ok[_B]]) -> Result[_B]:
        return f(x.value)

    def map(self, f: Callable[[_A], _B]) -> Result[_B]:
        return Ok(f(self.value))

    def and_then(self, f: Callable[[_A], Ok[_B]]) -> Result[_B]:
        return f(self.value)

    def then(self, x: Ok[_B]) -> Result[_B]:
        return x

    def unwrap(self) -> _A:
        return self.value


class Error(Result[Any]):
    def __init__(self, exception: Exception = Exception()):
        self.exception = exception

    def __repr__(self) -> str:
        return "Error"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Error) -> Result[Any]:
        return Error()

    @staticmethod
    def pure(x: _A) -> Result[Any]:
        return Error()

    @staticmethod
    def ap(f: Error, x: Error) -> Result[Any]:
        return Error()

    @staticmethod
    def bind(x: Error, f: Callable[[_A], Error]) -> Result[Any]:
        return Error()

    def map(self, f: Callable[[_A], _B]) -> Result[Any]:
        return Error()

    def and_then(self, f: Callable[[_A], Error]) -> Result[Any]:
        return Error()

    def then(self, x: Error) -> Result[Any]:
        return Error()

    def unwrap(self) -> None:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")


Result_42 = Ok(42)
Result_42_ = Error()

if __name__ == "__main__":
    if Result_42:
        print(Result_42.unwrap())
    else:
        print("Nothing")

    if Result_42_:
        print(Result_42_.unwrap())
    else:
        print("Nothing")

    Result_21 = Result_42.map(lambda x: x // 2)

    def _Result_int(x: int) -> Result[int]:
        return Ok(x)

    Result_int = _Result_int(42)

    Result_21 = Result_int.map(lambda x: x // 2)


def result(f: Callable):  # -> Callable[..., Any | Exception]:
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return e

    return wrapper


@result
def sqrt(x: float) -> Result[float]:
    if x < 0:
        raise ValueError("sqrt: negative number")
    return x**0.5


if __name__ == "__main__":
    print(sqrt(4))
    print(sqrt(-4))
