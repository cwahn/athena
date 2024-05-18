from __future__ import annotations
from typing import Callable, Iterable, Iterator, List, Optional, TypeVar
import functools


_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")


# Sequence operations


# def filter_map(f: Callable[[A], Optional[A]], xs: Iterable[A]) -> Iterator[A]:
#     for x in xs:
#         if (y := f(x)) is not None:
#             yield y


# def foldl(f: Callable[[A, B], A], acc: A, xs: Iterable[B]) -> A:
#     return functools.reduce(f, xs, acc)


# def unique(seq: Iterable[A]) -> List[A]:
#     def add_unique(acc: List[A], item: A) -> List[A]:
#         if item not in acc:
#             acc.append(item)
#         return acc

#     return functools.reduce(add_unique, seq, [])

# 