from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Protocol, TypeVar

# from typeclass import Monad
from entoli.base.typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


class _Result(Monad[_A], Protocol[_A]):
    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A]) -> _Result[_B]: ...

    @staticmethod
    def pure(x: _A) -> _Result[_A]: ...

    @staticmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> _Result[_B]: ...

    @staticmethod
    def bind(x: Any[_A], f: Callable[[_A], _Result[_B]]) -> _Result[_B]: ...

    def map(self, f: Callable[[_A], _B]) -> _Result[_B]: ...

    def and_then(self, f: Callable[[_A], _Result[_B]]) -> _Result[_B]: ...

    def then(self, x: _Result[_B]) -> _Result[_B]: ...

    def or_else(self, f: Callable[[Err], _Result[_A]]) -> _Result[_A]: ...

    def unwrap(self) -> _A: ...

    def and_(self, x: _Result[_A]) -> _Result[_A]: ...

    def or_(self, x: _Result[_A]) -> _Result[_A]: ...


class Ok(_Result[_A]):
    def __init__(self, value: _A):
        self.value = value

    def __repr__(self) -> str:
        return f"Ok {self.value}"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return True

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Ok[_A]) -> _Result[_B]:
        return Ok(f(x.value))

    @staticmethod
    def pure(x: _A) -> _Result[_A]:
        return Ok(x)

    @staticmethod
    def ap(f: Ok[Callable[[_A], _B]], x: Ok[_A]) -> _Result[_B]:
        return Ok(f.value(x.value))

    @staticmethod
    def bind(x: Ok[_A], f: Callable[[_A], _Result[_B]]) -> _Result[_B]:
        return f(x.value)

    def map(self, f: Callable[[_A], _B]) -> _Result[_B]:
        return Ok(f(self.value))

    def and_then(self, f: Callable[[_A], _Result[_B]]) -> _Result[_B]:
        return f(self.value)

    def then(self, x: _Result[_B]) -> _Result[_B]:
        return x

    def or_else(self, f: Callable[[Err], _Result[_A]]) -> _Result[_A]:
        return self

    def unwrap(self) -> _A:
        return self.value

    def and_(self, x: _Result[_A]) -> _Result[_A]:
        return x

    def or_(self, x: _Result[_A]) -> _Result[_A]:
        return self


class Err(_Result[Any]):
    def __init__(self, exception: Exception = Exception()):
        self.exception = exception

    def __repr__(self) -> str:
        return f"Error {{{self.exception}}}"

    def __str__(self) -> str:
        return repr(self)

    def __bool__(self) -> bool:
        return False

    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Err) -> _Result[_B]:
        return Err()

    @staticmethod
    def pure(x: _A) -> _Result[Any]:
        return Err()

    @staticmethod
    def ap(f: Err, x: Err) -> _Result[Any]:
        return Err()

    @staticmethod
    def bind(x: Err, f: Callable[[_A], _Result[_B]]) -> _Result[_B]:
        return Err()

    def map(self, f: Callable[[_A], _B]) -> _Result[_B]:
        return Err()

    def and_then(self, f: Callable[[_A], _Result[_B]]) -> _Result[_B]:
        return Err()

    def then(self, x: _Result[_B]) -> _Result[_B]:
        return Err()

    def or_else(self, f: Callable[[Err], _Result[_A]]) -> _Result[_A]:
        return f(self)

    def unwrap(self) -> None:
        raise ValueError("Nothing.unwrap: cannot unwrap Nothing")

    def and_(self, x: _Result[_A]) -> _Result[_A]:
        return Err()

    def or_(self, x: _Result[_A]) -> _Result[_A]:
        return x


Result = Ok | Err


def result(f: Callable):  # -> Callable[..., Any | Exception]:
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return e

    return wrapper


# Result_42 = Ok(42)
# Result_42_ = Error()

# if __name__ == "__main__":
#     if Result_42:
#         print(Result_42.unwrap())
#     else:
#         print("Nothing")

#     if Result_42_:
#         print(Result_42_.unwrap())
#     else:
#         print("Nothing")

#     Result_21 = Result_42.map(lambda x: x // 2)

#     def _Result_int(x: int) -> Result[int]:
#         return Ok(x)

#     Result_int = _Result_int(42)

#     Result_21 = Result_int.map(lambda x: x // 2)


# @result
# def sqrt(x: float) -> Result[float]:
#     if x < 0:
#         raise ValueError("sqrt: negative number")
#     return x**0.5


# if __name__ == "__main__":
#     print(sqrt(4))
#     print(sqrt(-4))
