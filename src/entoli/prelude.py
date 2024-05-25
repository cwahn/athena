import json
from typing import Any, List, Tuple, TypeVar, Iterable, Callable, Optional, Iterator
import functools

from dataclasses import dataclass
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.base.seq import Seq
from entoli.base.typeclass import Ord

_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")

# map and filter are already built-in functions in Python


def map(f: Callable[[_A], _B], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (f(x) for x in xs))


def filter_(f: Callable[[_A], bool], xs: Iterable[_A]) -> Iterable[_A]:
    # return Seq(lambda: (x for x in xs if f(x)))
    return Seq(lambda: filter(f, xs))


def filter_map(f: Callable[[_A], Maybe[_B]], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (y.unwrap() for x in xs if (y := f(x))))


def foldl(f: Callable[[_A, _B], _A], acc: _A, xs: Iterable[_B]) -> _A:
    return functools.reduce(f, xs, acc)


def head(xs: Iterable[_A]) -> _A:
    return next(iter(xs))


def tail(xs: Iterable[_A]) -> Iterable[_A]:
    def _tail():
        it = iter(xs)
        next(it)
        return it

    return Seq(_tail)


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


# ! For some reason, reversed iterator is not working with pattern matching correctly
def reverse(xs: Iterable[_A]) -> Iterable[_A]:
    return list(reversed(list(xs)))


def take(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def _take():
        it = iter(xs)
        for _ in range(n):
            yield next(it)

    return Seq(_take)


def drop(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def _drop():
        it = iter(xs)
        for _ in range(n):
            next(it)
        return it

    return Seq(_drop)


def elem(x: _A, xs: Iterable[_A]) -> bool:
    return x in xs


def _test_elem():
    assert not elem(1, [])
    assert elem(1, [1, 2, 3])
    assert not elem(4, [1, 2, 3])

    @dataclass
    class PyIdent:
        module: List[str]
        qual_name: List[str]

    ident_0 = PyIdent(
        module=["auto_generated", "some_package", "some_module"], qual_name=["greet_0"]
    )
    ident_1 = PyIdent(
        module=["auto_generated", "some_package", "some_module"], qual_name=["greet_1"]
    )

    assert elem(ident_0, [ident_0, ident_1])
    assert not elem(ident_0, [ident_1])


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


def zip_with(
    f: Callable[[_A, _B], _C], xs: Iterable[_A], ys: Iterable[_B]
) -> Iterable[_C]:
    return Seq(lambda: (f(x, y) for x, y in zip(xs, ys)))

def _test_zip_with():
    assert zip_with(lambda x, y: x + y, [], []) == []
    assert zip_with(lambda x, y: x + y, [1], []) == []
    assert zip_with(lambda x, y: x + y, [], [1]) == []
    assert zip_with(lambda x, y: x + y, [1], [2]) == [3]
    assert zip_with(lambda x, y: x + y, [1, 2], [3, 4]) == [4, 6]


def unzip(pairs: Iterable[Tuple[_A, _B]]) -> Tuple[Iterable[_A], Iterable[_B]]:
    a, b = zip(*pairs)
    return Seq(lambda: iter(a)), Seq(lambda: iter(b))


def concat(xss: Iterable[Iterable[_A]]) -> Iterable[_A]:
    return Seq(lambda: (x for xs in xss for x in xs))


def _test_concat():
    assert concat([]) == []
    assert concat([[], []]) == []
    assert concat([[1], [2]]) == [1, 2]
    assert concat([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    assert concat([[1, 2], [3, 4], [5, 6]]) == [1, 2, 3, 4, 5, 6]


def intersperse(x: _A, xs: Iterable[_A]) -> Iterable[_A]:
    def _intersperse():
        it = iter(xs)
        try:
            yield next(it)
            for y in it:
                yield x
                yield y
        except StopIteration:
            return

    return Seq(_intersperse)


def intercalate(sep: Iterable[_A], xss: Iterable[Iterable[_A]]) -> Iterable[_A]:
    def _intercalate():
        it = iter(xss)
        try:
            yield from next(it)
            for xs in it:
                yield from sep
                yield from xs
        except StopIteration:
            return

    return Seq(_intercalate)


def transpose(xss: Iterable[Iterable[_A]]) -> Iterable[Iterable[_A]]:
    if not xss:
        return Seq(lambda: iter([]))
    return Seq(lambda: (iter(x) for x in zip(*xss)))


# Additional functions


def unique(seq: Iterable[_A]) -> Iterable[_A]:
    def _unique(acc: Iterable[_A], x: _A) -> Iterable[_A]:
        if x not in acc:
            return (*acc, x)
        return acc

    return foldl(_unique, (), seq)


_Ord_A = TypeVar("_Ord_A", bound=Ord | int)
_Ord_B = TypeVar("_Ord_B", bound=Ord | int)


def sort(seq: Iterable[_Ord_A]) -> Iterable[_Ord_A]:
    return Seq.from_list(sorted(seq))


def sort_on(f: Callable[[_A], _Ord_B], seq: Iterable[_A]) -> Iterable[_A]:
    return Seq.from_list(sorted(seq, key=f))


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


def append(xs: Iterable[_A], x: _A) -> Iterable[_A]:
    def _append():
        yield from xs
        yield x

    return Seq(_append)


def _test_append():
    assert append([], 1) == [1]
    assert append([1], 2) == [1, 2]
    assert append([1, 2], 3) == [1, 2, 3]


def for_each(f: Callable[[_A], None], xs: Iterable[_A]) -> None:
    for x in xs:
        f(x)


def if_else(cond: bool, t: _A, f: _A) -> _A:
    return t if cond else f


def body(*exps):
    return [exp for exp in exps][-1]


def pstr(x: _A) -> str:
    def _to_dict(obj: _A) -> Any:
        if isinstance(obj, list):
            return [_to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: _to_dict(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            return {k: _to_dict(v) for k, v in obj.__dict__.items()}
        else:
            return obj

    return json.dumps(_to_dict(x), indent=2, default=str)
