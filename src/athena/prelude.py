from typing import Tuple, TypeVar, Iterable, Callable, Optional, Iterator
import functools

_A = TypeVar("_A")
_B = TypeVar("_B")

# map and filter are already built-in functions in Python


def filter_map(f: Callable[[_A], Optional[_A]], xs: Iterable[_A]) -> Iterator[_A]:
    for x in xs:
        if (y := f(x)) is not None:
            yield y


def foldl(f: Callable[[_A, _B], _A], acc: _A, xs: Iterable[_B]) -> _A:
    return functools.reduce(f, xs, acc)


def head(xs: Iterable[_A]) -> _A:
    return next(iter(xs))


def tail(xs: Iterable[_A]) -> Iterator[_A]:
    it = iter(xs)
    next(it)
    return it


def init(xs: Iterable[_A]) -> Iterator[_A]:
    it = iter(xs)
    prev = next(it)
    for curr in it:
        yield prev
        prev = curr


def last(xs: Iterable[_A]) -> _A:
    return functools.reduce(lambda _, x: x, xs)


def length(xs: Iterable[_A]) -> int:
    return sum(1 for _ in xs)


def null(xs: Iterable[_A]) -> bool:
    return not any(True for _ in xs)


def reverse(xs: Iterable[_A]) -> Iterator[_A]:
    return iter(reversed(list(xs)))


def take(n: int, xs: Iterable[_A]) -> Iterator[_A]:
    it = iter(xs)
    for _ in range(n):
        yield next(it)


def drop(n: int, xs: Iterable[_A]) -> Iterator[_A]:
    it = iter(xs)
    for _ in range(n):
        next(it)
    return it


def elem(x: _A, xs: Iterable[_A]) -> bool:
    return any(x == y for y in xs)


def not_elem(x: _A, xs: Iterable[_A]) -> bool:
    return all(x != y for y in xs)


def zip(xs: Iterable[_A], ys: Iterable[_B]) -> Iterator[Tuple[_A, _B]]:
    return iter(zip(xs, ys))


def unzip(pairs: Iterable[Tuple[_A, _B]]) -> Tuple[Iterator[_A], Iterator[_B]]:
    a, b = zip(*pairs)
    return iter(a), iter(b)  # type: ignore


def concat(xss: Iterable[Iterable[_A]]) -> Iterator[_A]:
    for xs in xss:
        for x in xs:
            yield x


def intersperse(x: _A, xs: Iterable[_A]) -> Iterator[_A]:
    it = iter(xs)
    try:
        yield next(it)
        for y in it:
            yield x
            yield y
    except StopIteration:
        return


def intercalate(sep: Iterable[_A], xss: Iterable[Iterable[_A]]) -> Iterator[_A]:
    it = iter(xss)
    try:
        yield from next(it)
        for xs in it:
            yield from sep
            yield from xs
    except StopIteration:
        return


def transpose(xss: Iterable[Iterable[_A]]) -> Iterator[Iterator[_A]]:
    if not xss:
        return iter([])
    return iter(map(iter, zip(*xss)))


# Additional functions


def unique(seq: Iterable[_A]) -> Iterator[_A]:
    seen = set()
    for x in seq:
        if x not in seen:
            seen.add(x)
            yield x
