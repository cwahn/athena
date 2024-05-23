from typing import Tuple, TypeVar, Iterable, Callable, Optional, Iterator
import functools

from entoli.base.maybe import Just, Maybe, Nothing
from entoli.base.seq import Seq

_A = TypeVar("_A")
_B = TypeVar("_B")

# map and filter are already built-in functions in Python


def map(f: Callable[[_A], _B], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (f(x) for x in xs))


def filter(f: Callable[[_A], bool], xs: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: (x for x in xs if f(x)))


# def filter_map(f: Callable[[_A], Optional[_A]], xs: Iterable[_A]) -> Iterator[_A]:
#     for x in xs:
#         if (y := f(x)) is not None:
#             yield y


def filter_map(f: Callable[[_A], Maybe[_B]], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (y.unwrap() for x in xs if (y := f(x))))


def foldl(f: Callable[[_A, _B], _A], acc: _A, xs: Iterable[_B]) -> _A:
    return functools.reduce(f, xs, acc)


def head(xs: Iterable[_A]) -> _A:
    return next(iter(xs))


# def tail(xs: Iterable[_A]) -> Iterator[_A]:
#     it = iter(xs)
#     next(it)
#     return it


def tail(xs: Iterable[_A]) -> Iterable[_A]:
    def tail_():
        it = iter(xs)
        next(it)
        return it

    return Seq(tail_)


# def init(xs: Iterable[_A]) -> Iterator[_A]:
#     it = iter(xs)
#     prev = next(it)
#     for curr in it:
#         yield prev
#         prev = curr


def init(xs: Iterable[_A]) -> Iterable[_A]:
    def init_():
        it = iter(xs)
        prev = next(it)
        for curr in it:
            yield prev
            prev = curr

    return Seq(init_)


def last(xs: Iterable[_A]) -> _A:
    return functools.reduce(lambda _, x: x, xs)


def length(xs: Iterable[_A]) -> int:
    return sum(1 for _ in xs)


def null(xs: Iterable[_A]) -> bool:
    return not any(True for _ in xs)


# def reverse(xs: Iterable[_A]) -> Iterator[_A]:
#     return iter(reversed(list(xs)))


# ! For some reason, reversed iterator is not working with pattern matching correctly
def reverse(xs: Iterable[_A]) -> Iterable[_A]:
    return list(reversed(list(xs)))


# def take(n: int, xs: Iterable[_A]) -> Iterator[_A]:
#     it = iter(xs)
#     for _ in range(n):
#         yield next(it)


def take(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def take_():
        it = iter(xs)
        for _ in range(n):
            yield next(it)

    return Seq(take_)


# def drop(n: int, xs: Iterable[_A]) -> Iterator[_A]:
#     it = iter(xs)
#     for _ in range(n):
#         next(it)
#     return it


def drop(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def drop_():
        it = iter(xs)
        for _ in range(n):
            next(it)
        return it

    return Seq(drop_)


def elem(x: _A, xs: Iterable[_A]) -> bool:
    return x in xs


def not_elem(x: _A, xs: Iterable[_A]) -> bool:
    return x not in xs


def find(f: Callable[[_A], bool], xs: Iterable[_A]) -> Maybe[_A]:
    for x in xs:
        if f(x):
            return Just(x)
    return Nothing()


def find_index(f: Callable[[_A], bool], xs: Iterable[_A]) -> Maybe[int]:
    for i, x in enumerate(xs):
        if f(x):
            return Just(i)
    return Nothing()


# def unzip(pairs: Iterable[Tuple[_A, _B]]) -> Tuple[Iterator[_A], Iterator[_B]]:
#     a, b = zip(*pairs)
#     return iter(a), iter(b)  # type: ignore


def unzip(pairs: Iterable[Tuple[_A, _B]]) -> Tuple[Iterable[_A], Iterable[_B]]:
    a, b = zip(*pairs)
    return Seq(lambda: iter(a)), Seq(lambda: iter(b))


# def concat(xss: Iterable[Iterable[_A]]) -> Iterator[_A]:
#     for xs in xss:
#         for x in xs:
#             yield x


def concat(xss: Iterable[Iterable[_A]]) -> Iterable[_A]:
    return Seq(lambda: (x for xs in xss for x in xs))


# def intersperse(x: _A, xs: Iterable[_A]) -> Iterator[_A]:
#     it = iter(xs)
#     try:
#         yield next(it)
#         for y in it:
#             yield x
#             yield y
#     except StopIteration:
#         return


def intersperse(x: _A, xs: Iterable[_A]) -> Iterable[_A]:
    def intersperse_():
        it = iter(xs)
        try:
            yield next(it)
            for y in it:
                yield x
                yield y
        except StopIteration:
            return

    return Seq(intersperse_)


# def intercalate(sep: Iterable[_A], xss: Iterable[Iterable[_A]]) -> Iterator[_A]:
#     it = iter(xss)
#     try:
#         yield from next(it)
#         for xs in it:
#             yield from sep
#             yield from xs
#     except StopIteration:
#         return


def intercalate(sep: Iterable[_A], xss: Iterable[Iterable[_A]]) -> Iterable[_A]:
    def intercalate_():
        it = iter(xss)
        try:
            yield from next(it)
            for xs in it:
                yield from sep
                yield from xs
        except StopIteration:
            return

    return Seq(intercalate_)


# def transpose(xss: Iterable[Iterable[_A]]) -> Iterator[Iterator[_A]]:
#     if not xss:
#         return iter([])
#     return iter(map(iter, zip(*xss)))


def transpose(xss: Iterable[Iterable[_A]]) -> Iterable[Iterable[_A]]:
    if not xss:
        return Seq(lambda: iter([]))
    return Seq(lambda: (iter(x) for x in zip(*xss)))


# Additional functions


def unique(seq: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: (x for x in set(seq)))


def sort(seq: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: sorted(seq))  # type: ignore


def sort_on(f: Callable[[_A], _B], seq: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: sorted(seq, key=f))  # type: ignore


def is_prefix_of(xs: Iterable[_A], ys: Iterable[_A]) -> bool:
    match xs:
        case []:
            return True
        case [x, *xs_]:
            match ys:
                case []:
                    return False
                case [y, *ys_]:
                    if x == y:
                        return is_prefix_of(xs_, ys_)
                    else:
                        return False

    raise RuntimeError(f"Unreachable code: {xs}{list(xs)}, {ys}{list(ys)} ")


def _test_is_prefix_of():
    assert is_prefix_of([], [])
    assert is_prefix_of([], [1])
    assert is_prefix_of([1], [1])
    assert is_prefix_of([1, 2], [1, 2])
    assert is_prefix_of([1, 2], [1, 2, 3])
    assert not is_prefix_of([1, 2], [1])
    assert not is_prefix_of([1, 2], [1, 3])
    assert not is_prefix_of([1, 2], [1, 3, 4])


def is_suffix_of(xs: Iterable[_A], ys: Iterable[_A]) -> bool:
    return is_prefix_of(reverse(xs), reverse(ys))


def _test_is_suffix_of():
    assert is_suffix_of([], [])
    assert is_suffix_of([], [1])
    assert is_suffix_of([1], [1])
    assert is_suffix_of([1, 2], [1, 2])
    assert is_suffix_of([1, 2], [0, 1, 2])
    assert not is_suffix_of([1, 2], [1])
    assert not is_suffix_of([1, 2], [3, 1])
    assert not is_suffix_of([1, 2], [4, 3, 1])


def fst(pair: Tuple[_A, _B]) -> _A:
    return pair[0]


def snd(pair: Tuple[_A, _B]) -> _B:
    return pair[1]


# Others


def for_each(f: Callable[[_A], None], xs: Iterable[_A]) -> None:
    for x in xs:
        f(x)


def if_else(cond: bool, t: _A, f: _A) -> _A:
    return t if cond else f


def body(*exps):
    return [exp for exp in exps][-1]
