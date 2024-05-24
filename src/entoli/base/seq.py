from collections.abc import Sequence
from re import L
from typing import Callable, Generic, Iterable, Iterator, List, Type, TypeVar

_A = TypeVar("_A")


class Seq(Generic[_A], Sequence):
    """A resuable iterable"""

    def __init__(self, f: Callable[[], Iterator[_A]]):
        self.f = f

    def __iter__(self):
        return self.f()

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __getitem__(self, idx):
        return list(self)[idx]

    def __eq__(self, other):
        if isinstance(other, Seq):
            return self.eval() == other.eval()
        elif isinstance(other, list):
            return self.eval() == other
        else:
            raise TypeError(f"Cannot compare Seq with {type(other)}")

    def eval(self) -> Iterable[_A]:
        if self._cached_list is None:
            self._cached_list = list(self.f())
        return self._cached_list

    @staticmethod
    def from_list(xs: List[_A]) -> "Seq[_A]":
        def generator() -> Iterator[_A]:
            return iter(xs)

        seq = Seq(generator)
        seq._cached_list = xs
        return seq
