from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Iterable, Iterator, Set, TypeVar, Tuple

from entoli.base.seq import Seq

_A = TypeVar("_A")
_B = TypeVar("_B")


# todo Need extra optimization
@dataclass
class Map(Generic[_A, _B]):
    inner: list[Tuple[_A, _B]]

    def __iter__(self) -> Iterator[Tuple[_A, _B]]:
        return self.inner.__iter__()

    def __contains__(self, item: _A) -> bool:
        return item in self.keys()

    def __getitem__(self, key: _A) -> _B:
        for k, v in self.inner:
            if k == key:
                return v
        raise KeyError(key)

    def __setitem__(self, key: _A, value: _B):
        if key in self.keys():
            del self[key]

        self.inner.append((key, value))
        # self.inner.add((key, value))

    def __delitem__(self, key: _A):
        for k, _ in self.inner:
            if k == key:
                self.inner.remove((k, _))
                return
        raise KeyError(key)

    def __len__(self):
        return len(self.inner)

    def __bool__(self):
        return bool(self.inner)

    @staticmethod
    def from_iter(items: Iterable[Tuple[_A, _B]]) -> "Map[_A, _B]":
        return Map(list(items))

    def items(self) -> Iterable[Tuple[_A, _B]]:
        return Seq(lambda: (item for item in self.inner))

    def keys(self) -> Iterable[_A]:
        return Seq(lambda: (k for k, _ in self.inner))

    def values(self) -> Iterable[_B]:
        return Seq(lambda: (v for _, v in self.inner))


def test_Map_construct():
    m = Map.from_iter([(1, 2), (3, 4)])
    assert len(m) == 2
    assert 1 in m
    assert 2 not in m
    assert m[1] == 2
    assert m[3] == 4
    assert list(m.items()) == [(1, 2), (3, 4)]
    assert list(m.keys()) == [1, 3]
    assert list(m.values()) == [2, 4]


def test_Map_set():
    m = Map.from_iter([(1, 2), (3, 4)])
    m[1] = 3
    assert len(m) == 2
    assert m[1] == 3
    m[5] = 6
    assert len(m) == 3
    assert m[5] == 6


def test_Map_del():
    m = Map.from_iter([(1, 2), (3, 4)])
    del m[1]
    assert len(m) == 1
    assert 1 not in m
    assert 3 in m
    del m[3]
    assert len(m) == 0
    assert 3 not in m
    assert 1 not in m


def test_Map_iter():
    m = Map.from_iter([(1, 2), (3, 4)])
    assert list(m) == [(1, 2), (3, 4)]


def test_Map_bool():
    m = Map.from_iter([(1, 2), (3, 4)])
    assert m
    m = Map.from_iter([])
    assert not m
    m = Map.from_iter([(1, 2)])
    assert m
    del m[1]
    assert not m
