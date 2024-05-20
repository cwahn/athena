from typing import Callable, Generic, Iterator, Type, TypeVar

_A = TypeVar("_A")


class Seq(Generic[_A]):
    """A resuable iterable"""

    def __init__(self, f: Callable[[], Iterator[_A]]):
        self.f = f

    def __iter__(self):
        return self.f()
