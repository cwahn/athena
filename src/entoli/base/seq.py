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

    @staticmethod
    def from_list(xs: List[_A]) -> "Seq[_A]":
        def generator() -> Iterator[_A]:
            return iter(xs)

        return Seq(generator, xs)

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

    def __add__(self, other: Iterable[_A]) -> "Seq[_A]":
        def concat_generator() -> Iterator[_A]:
            yield from self
            yield from other

        return Seq(concat_generator)

    # ! Mutating operation is not allowed
    # def __iadd__(self, other: "Seq[_A]") -> "Seq[_A]":
    #     def concat_generator() -> Iterator[_A]:
    #         yield from self
    #         yield from other

    #     # Create a new Seq with combined generator and reassign it to self
    #     new_seq = Seq(concat_generator)
    #     self.f = new_seq.f
    #     self._cached_list = None  # Invalidate the cache
    #     return self

    def __bool__(self) -> bool:
        return any(True for _ in self)

    def __repr__(self) -> str:
        return f"Seq({list(self)})"

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __copy__(self) -> "Seq[_A]":
        return Seq(self.f, self._cached_list)

    def __deepcopy__(self, memo) -> "Seq[_A]":
        return Seq(self.f, self._cached_list)

    def __reversed__(self) -> Iterator[_A]:
        if self._cached_list is not None:
            return reversed(self._cached_list)
        else:
            self._cached_list = list(self.f())
            return reversed(self._cached_list)


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

    def _test___add__(self):
        seq0 = Seq.from_list([])
        seq1 = Seq.from_list([1, 2, 3])
        seq2 = Seq.from_list([4, 5, 6])

        assert seq0 + seq1 == seq1
        assert seq1 + seq0 == seq1
        assert seq1 + seq2 == Seq.from_list([1, 2, 3, 4, 5, 6])
