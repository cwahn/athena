from collections.abc import Sequence
from typing import Callable, Generic, Iterable, Iterator, List, Optional, Type, TypeVar

_A = TypeVar("_A")


class Seq(Generic[_A], Sequence):
    """A resuable iterable"""

    def __init__(
        self, f: Callable[[], Iterator[_A]], cached_list: Optional[List[_A]] = None
    ):
        self.f = f
        self._cached_list = cached_list

    def __iter__(self):
        if self._cached_list is not None:
            return iter(self._cached_list)
        else:
            return self.f()

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __getitem__(self, idx):
        return list(self)[idx]

    def __contains__(self, value: object) -> bool:
        if self._cached_list is not None:
            return value in self._cached_list
        else:
            return any(value == x for x in self.f())

    def eval(self) -> Iterable[_A]:
        if self._cached_list is None:
            self._cached_list = list(self.f())
        return self._cached_list

    def __eq__(self, other):
        if isinstance(other, Seq):
            return self.eval() == other.eval()
        elif isinstance(other, list):
            return self.eval() == other
        else:
            raise TypeError(f"Cannot compare Seq with {type(other)}")

    @staticmethod
    def from_list(xs: List[_A]) -> "Seq[_A]":
        def generator() -> Iterator[_A]:
            return iter(xs)

        seq = Seq(generator, xs)
        return seq


class _TestSeq:
    def _test_as_bool(self):
        seq = Seq.from_list([1, 2, 3])
        if seq:
            assert True
        else:
            assert False

        if not seq:
            assert False
        else:
            assert True

        empty_seq = Seq.from_list([])
        if empty_seq:
            assert False
        else:
            assert True

        if not empty_seq:
            assert True
        else:
            assert False
