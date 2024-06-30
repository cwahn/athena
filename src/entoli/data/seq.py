from __future__ import annotations
from collections.abc import Sequence
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    TypeVar,
)

from entoli.base.typeclass import Monad

_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass(frozen=True)
class Seq(Generic[_A], Monad[_A], Sequence):
    """A resuable iterable"""

    _generator: Callable[[], Iterator[_A]]

    def __iter__(self):
        return self._generator()

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __getitem__(self, idx):
        return list(self)[idx]

    def __contains__(self, value: object) -> bool:
        return any(value == x for x in self._generator())

    def __eq__(self, other):
        return self.list() == list(other)

    def __add__(self, other: Iterable[_A]) -> Seq[_A]:
        def concat_generator() -> Iterator[_A]:
            yield from self
            yield from other

        return Seq(concat_generator)

    # ! Mutating operation is not allowed
    # def __iadd__(self, other: Seq[_A]) -> Seq[_A]:
    #     self._cached_list = list(self) + list(other)

    def __bool__(self) -> bool:
        return any(True for _ in self)

    def __repr__(self) -> str:
        return f"Seq({list(self)})"

    def __str__(self) -> str:
        return self.__repr__()

    def __hash__(self) -> int:
        return hash(tuple(self))

    def __copy__(self) -> Seq[_A]:
        return Seq(self._generator)

    def __deepcopy__(self, memo) -> Seq[_A]:
        return Seq(self._generator)

    def __reversed__(self) -> Iterator[_A]:
        """
        Return a reversed iterator of the sequence
        Not recommended to use this method since it will evaluate the whole sequence
        Instead, evaluate the seq explicitly with list() and then reverse it
        """

        return reversed(list(self))

    @staticmethod
    def from_iterable(xs: Iterable[_A]) -> Seq[_A]:
        def generator() -> Iterator[_A]:
            return iter(xs)

        return Seq(generator)

    def list(self) -> Iterable[_A]:
        return list(self._generator())

    def fmap(self, f: Callable[[_A], _B]) -> Seq[_B]:
        def generator() -> Iterator[_B]:
            for x in self:
                yield f(x)

        return Seq(generator)

    @staticmethod
    def pure(x: _A) -> Seq[_A]:
        return Seq.from_iterable([x])

    def ap(self, f: Seq[Callable[[_A], _B]]) -> Seq[_B]:
        def generator() -> Iterator[_B]:
            for x in self:
                for y in f:
                    yield y(x)

        return Seq(generator)

    def and_then(self, f: Callable[[_A], Seq[_B]]) -> Seq[_B]:
        def generator() -> Iterator[_B]:
            for x in self:
                for y in f(x):
                    yield y

        return Seq(generator)


class _TestSeq:
    def _test_as_bool(self):
        seq = Seq.from_iterable([1, 2, 3])
        if seq:
            assert True
        else:
            assert False

        if not seq:
            assert False
        else:
            assert True

        empty_seq = Seq.from_iterable([])
        if empty_seq:
            assert False
        else:
            assert True

        if not empty_seq:
            assert True
        else:
            assert False

    def _test___add__(self):
        seq0 = Seq.from_iterable([])
        seq1 = Seq.from_iterable([1, 2, 3])
        seq2 = Seq.from_iterable([4, 5, 6])

        assert seq0 + seq1 == seq1
        assert seq1 + seq0 == seq1
        assert seq1 + seq2 == Seq.from_iterable([1, 2, 3, 4, 5, 6])

    def _test_fmap(self):
        seq_0 = Seq(lambda: iter([]))
        assert seq_0.fmap(lambda x: x + 1) == []

        seq_1 = Seq.from_iterable([1, 2, 3])
        assert seq_1.fmap(lambda x: x + 1) == [2, 3, 4]

    def _test_pure(self):
        assert Seq.pure(1) == [1]

    def _test_ap(self):
        seq_0 = Seq.from_iterable([])
        seq_1 = Seq.from_iterable([1, 2, 3])

        fs = Seq.from_iterable([lambda x: x + 1, lambda x: x * 2])

        assert seq_0.ap(fs) == []
        assert seq_1.ap(fs) == [2, 2, 3, 4, 4, 6]

    def _test_and_then(self):
        seq_0 = Seq.from_iterable([])
        seq_1 = Seq.from_iterable([1, 2, 3])

        def get_smaller(x):
            return Seq.from_iterable([i for i in range(x)])

        assert seq_0.and_then(get_smaller) == []
        assert seq_1.and_then(get_smaller) == [0, 0, 1, 0, 1, 2]
