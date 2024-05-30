import builtins
import json
from operator import le
import re
from typing import Any, List, Tuple, TypeVar, Iterable, Callable, Optional, Iterator
import functools

from dataclasses import dataclass

from entoli.base.io import Io
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.base.seq import Seq
from entoli.base.typeclass import Ord


_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")

# Tuple


def fst(pair: Tuple[_A, _B]) -> _A:
    return pair[0]


def _test_fst():
    assert fst((1, 2)) == 1


def snd(pair: Tuple[_A, _B]) -> _B:
    return pair[1]


def _test_snd():
    assert snd((1, 2)) == 2


def curry(f: Callable[[_A, _B], _C]) -> Callable[[_A], Callable[[_B], _C]]:
    return lambda x: lambda y: f(x, y)


def _test_curry():
    def _add(x, y):
        return x + y

    assert curry(_add)(1)(2) == 3  # type : ignore


def uncurry(f: Callable[[_A], Callable[[_B], _C]]) -> Callable[[_A, _B], _C]:
    return lambda x, y: f(x)(y)


def _test_uncurry():
    assert uncurry(lambda x: lambda y: x + y)(1, 2) == 3  # type: ignore


# Folds and traversals


def foldl(f: Callable[[_A, _B], _A], acc: _A, xs: Iterable[_B]) -> _A:
    return functools.reduce(f, xs, acc)


def _test_foldl():
    assert foldl(lambda acc, x: acc + x, 0, []) == 0
    assert foldl(lambda acc, x: acc + x, 0, [1]) == 1
    assert foldl(lambda acc, x: acc + x, 0, [1, 2, 3]) == 6


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


# maximum, minimum, sum, product, any, all are built-in functions


# Miscellaneous functions


def id(x: _A) -> _A:
    return x


# List operations


def map(f: Callable[[_A], _B], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: builtins.map(f, xs))


def _test_map():
    assert map(lambda x: x + 1, []) == []
    assert map(lambda x: x + 1, [1]) == [2]
    assert map(lambda x: x + 1, [1, 2]) == [2, 3]


def append(xs: Iterable[_A], ys: Iterable[_A]) -> Iterable[_A]:
    def _append():
        yield from xs
        yield from ys

    return Seq(_append)


def _test_append():
    assert append([], []) == []
    assert append([], [1]) == [1]
    assert append([1], []) == [1]
    assert append([1], [2]) == [1, 2]
    assert append([1, 2], [3, 4]) == [1, 2, 3, 4]


def filter(f: Callable[[_A], bool], xs: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: builtins.filter(f, xs))


def _test_filter():
    assert filter(lambda x: x % 2 == 0, []) == []
    assert filter(lambda x: x % 2 == 0, [1]) == []
    assert filter(lambda x: x % 2 == 0, [1, 2]) == [2]
    assert filter(lambda x: x % 2 == 0, [1, 2, 3, 4]) == [2, 4]


def head(xs: Iterable[_A]) -> _A:
    """
    Return the first element of the iterable.
    The iterable must not be empty.
    """
    return next(iter(xs))


def _test_head():
    try:
        head([])
        assert False
    except StopIteration:
        assert True

    assert head([1]) == 1
    assert head([1, 2]) == 1


def last(xs: Iterable[_A]) -> _A:
    """
    Return the last element of the iterable.
    The iterable must not be empty.
    """
    return functools.reduce(lambda _, x: x, xs)


def _test_last():
    try:
        last([])
        assert False
    except TypeError:
        assert True

    assert last([1]) == 1
    assert last([1, 2]) == 2
    assert last([1, 2, 3]) == 3


def tail(xs: Iterable[_A]) -> Iterable[_A]:
    """
    Return all elements of the iterable except the first one.
    The iterable must be finite and non-empty.
    """

    def _tail():
        it = iter(xs)
        next(it)
        return it

    return Seq(_tail)


def _test_tail():
    # ! Applying tail to an empty list is undefined
    # ! Defining tail of an empty list if self will not raise an error
    # ! However, calling tail of an empty list will raise an error
    try:
        next(iter(tail([])))
        assert False
    except StopIteration:
        assert True

    assert tail([1]) == []
    assert tail([1, 2]) == [2]
    assert tail([1, 2, 3]) == [2, 3]


def init(xs: Iterable[_A]) -> Iterable[_A]:
    """
    Return all elements of the iterable except the last one.
    The iterable must be finite and non-empty.
    """

    def init_():
        it = iter(xs)
        prev = next(it)
        for curr in it:
            yield prev
            prev = curr

    return Seq(init_)


def _test_init():
    # ! Applying init to an empty list is undefined
    # ! Defining init of an empty list if self will not raise an error
    # ! However, calling init of an empty list will raise an error

    try:
        next(iter(init([])))
        assert False
    except Exception as e:
        assert True

    assert init([1]) == []
    assert init([1, 2]) == [1]
    assert init([1, 2, 3]) == [1, 2]


def nth(xs: Iterable[_A], n: int) -> _A:
    return next(x for i, x in enumerate(xs) if i == n)


def _test_nth():
    assert nth([1], 0) == 1
    assert nth([1, 2], 1) == 2
    assert nth([1, 2, 3], 2) == 3


def null(xs: Iterable[_A]) -> bool:
    return not any(True for _ in xs)


def _test_null():
    assert null([])
    assert not null([1])


def length(xs: Iterable[_A]) -> int:
    return sum(1 for _ in xs)


def _test_length():
    assert length([]) == 0
    assert length([1]) == 1
    assert length([1, 2]) == 2
    assert length([1, 2, 3]) == 3


def reverse(xs: Iterable[_A]) -> Iterable[_A]:
    return Seq(lambda: reversed(list(xs)))


def _test_reverse():
    assert reverse([]) == []
    assert reverse([1]) == [1]
    assert reverse([1, 2]) == [2, 1]
    assert reverse([1, 2, 3]) == [3, 2, 1]


# and, or, any, all are reserved keywords and built-in functions


def concat(xss: Iterable[Iterable[_A]]) -> Iterable[_A]:
    return Seq(lambda: (x for xs in xss for x in xs))


def _test_concat():
    assert concat([]) == []
    assert concat([[], []]) == []
    assert concat([[1], [2]]) == [1, 2]
    assert concat([[1, 2], [3, 4]]) == [1, 2, 3, 4]
    assert concat([[1, 2], [3, 4], [5, 6]]) == [1, 2, 3, 4, 5, 6]


def concat_map(f: Callable[[_A], Iterable[_B]], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (y for x in xs for y in f(x)))


def _test_concat_map():
    assert concat_map(lambda x: [], []) == []
    assert concat_map(lambda x: [], [1, 2]) == []
    assert concat_map(lambda x: [x + 1], []) == []
    assert concat_map(lambda x: [x + 1], [1]) == [2]
    assert concat_map(lambda x: [x + 1], [1, 2]) == [2, 3]
    assert concat_map(lambda x: [x + 1, x + 2], []) == []
    assert concat_map(lambda x: [x + 1, x + 2], [1, 2]) == [2, 3, 3, 4]


# Building lists

# todo scanl, scanl1, scanr, scanr1

# Infinite lists

# todo iterate, repeat, replicate, cycle

# Sublists


def take(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def _take():
        it = iter(xs)
        for _ in range(n):
            yield next(it)

    return Seq(_take)


def _test_take():
    assert take(0, []) == []
    assert take(0, [1]) == []
    assert take(1, [1]) == [1]
    assert take(1, [1, 2]) == [1]
    assert take(2, [1, 2]) == [1, 2]
    assert take(2, [1, 2, 3]) == [1, 2]


def drop(n: int, xs: Iterable[_A]) -> Iterable[_A]:
    def _drop():
        it = iter(xs)
        for _ in range(n):
            next(it)
        return it

    return Seq(_drop)


def _test_drop():
    assert drop(0, []) == []
    assert drop(0, [1]) == [1]
    assert drop(1, [1]) == []
    assert drop(1, [1, 2]) == [2]
    assert drop(2, [1, 2]) == []
    assert drop(2, [1, 2, 3]) == [3]


def take_while(f: Callable[[_A], bool], xs: Iterable[_A]) -> Iterable[_A]:
    def _take_while():
        it = iter(xs)
        for x in it:
            if f(x):
                yield x
            else:
                return

    return Seq(_take_while)


def _test_take_while():
    assert take_while(lambda x: x < 3, []) == []
    assert take_while(lambda x: x < 3, [1]) == [1]
    assert take_while(lambda x: x < 3, [1, 2]) == [1, 2]
    assert take_while(lambda x: x < 3, [1, 2, 3]) == [1, 2]


def drop_while(f: Callable[[_A], bool], xs: Iterable[_A]) -> Iterable[_A]:
    def _drop_while():
        it = iter(xs)
        for x in it:
            if not f(x):
                yield x
                break
        return it

    return Seq(_drop_while)


def _test_drop_while():
    assert drop_while(lambda x: x < 3, []) == []
    assert drop_while(lambda x: x < 3, [1]) == []
    assert drop_while(lambda x: x < 3, [1, 2]) == []
    assert drop_while(lambda x: x < 3, [1, 2, 3]) == [3]


def span(
    f: Callable[[_A], bool], xs: Iterable[_A]
) -> Tuple[Iterable[_A], Iterable[_A]]:
    return take_while(f, xs), drop_while(f, xs)


def _test_span():
    assert span(lambda x: x < 3, []) == ([], [])
    assert span(lambda x: x < 3, [1]) == ([1], [])
    assert span(lambda x: x < 3, [1, 2]) == ([1, 2], [])
    assert span(lambda x: x < 3, [1, 2, 3]) == ([1, 2], [3])


# no break since it is a keyword


def split_at(n: int, xs: Iterable[_A]) -> Tuple[Iterable[_A], Iterable[_A]]:
    return take(n, xs), drop(n, xs)


def _test_split_at():
    assert split_at(0, []) == ([], [])
    assert split_at(0, [1]) == ([], [1])
    assert split_at(1, [1]) == ([1], [])
    assert split_at(1, [1, 2]) == ([1], [2])
    assert split_at(2, [1, 2]) == ([1, 2], [])
    assert split_at(2, [1, 2, 3]) == ([1, 2], [3])


# Searching lists


def not_elem(x: _A, xs: Iterable[_A]) -> bool:
    return x not in xs


def _test_not_elem():
    assert not_elem(1, [])
    assert not not_elem(1, [1, 2, 3])
    assert not_elem(4, [1, 2, 3])


def lookup(x: _A, xs: Iterable[Tuple[_A, _B]]) -> Maybe[_B]:
    for k, v in xs:
        if k == x:
            return Just(v)
    return Nothing()


def _test_lookup():
    assert lookup(1, []) == Nothing()
    assert lookup(1, [(1, 2)]) == Just(2)
    assert lookup(1, [(2, 3)]) == Nothing()
    assert lookup(1, [(2, 3), (1, 2)]) == Just(2)


# Zipping and unzipping lists


def zip(xs: Iterable[_A], ys: Iterable[_B]) -> Iterable[Tuple[_A, _B]]:
    return Seq(lambda: builtins.zip(xs, ys))


def _test_zip():
    assert zip([], []) == []
    assert zip([1], []) == []
    assert zip([], [1]) == []
    assert zip([1], [2]) == [(1, 2)]
    assert zip([1, 2], [3, 4]) == [(1, 3), (2, 4)]


def zip_with(
    f: Callable[[_A, _B], _C], xs: Iterable[_A], ys: Iterable[_B]
) -> Iterable[_C]:
    return Seq(lambda: (f(x, y) for x, y in builtins.zip(xs, ys)))


def _test_zip_with():
    assert zip_with(lambda x, y: x + y, [], []) == []
    assert zip_with(lambda x, y: x + y, [1], []) == []
    assert zip_with(lambda x, y: x + y, [], [1]) == []
    assert zip_with(lambda x, y: x + y, [1], [2]) == [3]
    assert zip_with(lambda x, y: x + y, [1, 2], [3, 4]) == [4, 6]


def unzip(pairs: Iterable[Tuple[_A, _B]]) -> Tuple[Iterable[_A], Iterable[_B]]:
    if not pairs:
        return [], []
    else:

        def _a():
            for a, _ in pairs:
                yield a

        def _b():
            for _, b in pairs:
                yield b

        return Seq(_a), Seq(_b)


def _test_unzip():
    assert unzip([]) == ([], [])
    assert unzip([(1, 2)]) == ([1], [2])
    assert unzip([(1, 2), (3, 4)]) == ([1, 3], [2, 4])


# Functions on strings


def lines(s: str) -> Iterable[str]:
    return Seq.from_list(s.splitlines())


def _test_lines():
    assert lines("") == []
    assert lines("\n") == [""]
    assert lines("a\nb") == ["a", "b"]
    assert lines("a\nb\n") == ["a", "b"]  # ! Last empty line is removed


def words(s: str) -> Iterable[str]:
    return Seq.from_list(s.split())


def _test_words():
    assert words("") == []
    assert words("a") == ["a"]
    assert words("a b") == ["a", "b"]
    assert words("a b ") == ["a", "b"]


def unlines(xs: Iterable[str]) -> str:
    if not xs:
        return ""
    else:
        return "\n".join(xs)


def _test_unlines():
    assert unlines([]) == ""
    assert unlines([""]) == ""
    assert unlines(["a", "b"]) == "a\nb"
    assert unlines(["a", "b", ""]) == "a\nb\n"


def unwords(xs: Iterable[str]) -> str:
    return " ".join(xs).strip()


def _test_unwords():
    assert unwords([]) == ""
    assert unwords([""]) == ""
    assert unwords(["a"]) == "a"
    assert unwords(["a", "b"]) == "a b"
    assert unwords(["a", "b", ""]) == "a b"


# io


def put_str(s: str) -> Io[None]:
    return Io(lambda: print(s, end=""))


def put_strln(s: str) -> Io[None]:
    return Io(lambda: print(s))


get_str = Io(input)


# Additional functions


def filter_map(f: Callable[[_A], Maybe[_B]], xs: Iterable[_A]) -> Iterable[_B]:
    return Seq(lambda: (y.unwrap() for x in xs if (y := f(x))))


def _test_filter_map():
    assert filter_map(lambda x: Just(x + 1), []) == []
    assert filter_map(lambda x: Just(x + 1), [1]) == [2]
    assert filter_map(lambda x: Just(x + 1), [1, 2]) == [2, 3]
    assert filter_map(lambda x: Nothing(), [1, 2]) == []


def partition(
    f: Callable[[_A], bool], xs: Iterable[_A]
) -> Tuple[Iterable[_A], Iterable[_A]]:
    return filter(f, xs), filter(lambda x: not f(x), xs)


def _test_partition():
    assert partition(lambda x: x < 3, []) == ([], [])
    assert partition(lambda x: x < 3, [1]) == ([1], [])
    assert partition(lambda x: x < 3, [1, 2]) == ([1, 2], [])
    assert partition(lambda x: x < 3, [1, 2, 3]) == ([1, 2], [3])


def chunks_of(n: int, xs: Iterable[_A]) -> Iterable[Iterable[_A]]:
    def _chunk():
        it = iter(xs)
        while True:
            acc = []
            for _ in range(n):
                try:
                    acc.append(next(it))
                except StopIteration:
                    break
            if not acc:
                break
            yield acc

    return Seq(_chunk)


def _test_chunks_of():
    assert chunks_of(1, []) == []
    assert chunks_of(1, [1]) == [[1]]
    assert chunks_of(1, [1, 2]) == [[1], [2]]
    assert chunks_of(2, [1, 2, 3]) == [[1, 2], [3]]
    assert chunks_of(2, [1, 2, 3, 4]) == [[1, 2], [3, 4]]


def group(xs: Iterable[_A]) -> Iterable[Iterable[_A]]:
    def _group():
        it = iter(xs)
        try:
            prev = next(it)
            acc = [prev]
            for curr in it:
                if curr == prev:
                    acc.append(curr)
                else:
                    yield acc
                    acc = [curr]
                    prev = curr
            yield acc
        except StopIteration:
            return

    return Seq(_group)


def _test_group():
    assert group([]) == []
    assert group([1]) == [[1]]
    assert group([1, 1]) == [[1, 1]]
    assert group([1, 2]) == [[1], [2]]
    assert group([1, 1, 2, 2]) == [[1, 1], [2, 2]]
    assert group([1, 1, 2, 2, 1]) == [[1, 1], [2, 2], [1]]


def group_by(f: Callable[[_A], _B], xs: Iterable[_A]) -> Iterable[Iterable[_A]]:
    def _group_by():
        it = iter(xs)
        try:
            prev = next(it)
            prev_key = f(prev)
            acc = [prev]
            for curr in it:
                curr_key = f(curr)
                if curr_key == prev_key:
                    acc.append(curr)
                else:
                    yield acc
                    acc = [curr]
                    prev_key = curr_key
            yield acc
        except StopIteration:
            return

    return Seq(_group_by)


def _test_group_by():
    assert group_by(lambda x: x, []) == []
    assert group_by(lambda x: x, [1]) == [[1]]
    assert group_by(lambda x: x, [1, 1]) == [[1, 1]]
    assert group_by(lambda x: x, [1, 2]) == [[1], [2]]
    assert group_by(lambda x: x, [1, 1, 2, 2]) == [[1, 1], [2, 2]]
    assert group_by(lambda x: x, [1, 1, 2, 2, 1]) == [[1, 1], [2, 2], [1]]

    assert group_by(lambda x: x % 2, []) == []
    assert group_by(lambda x: x % 2, [1]) == [[1]]
    assert group_by(lambda x: x % 2, [1, 1]) == [[1, 1]]
    assert group_by(lambda x: x % 2, [1, 2]) == [[1], [2]]
    assert group_by(lambda x: x % 2, [1, 2, 3]) == [[1], [2], [3]]
    assert group_by(lambda x: x % 2, [1, 2, 2]) == [[1], [2, 2]]


def elem_index(x: _A, xs: Iterable[_A]) -> Maybe[int]:
    for i, y in enumerate(xs):
        if x == y:
            return Just(i)
    return Nothing()


def _test_elem_index():
    assert elem_index(1, []) == Nothing()
    assert elem_index(1, [1]) == Just(0)
    assert elem_index(1, [2]) == Nothing()
    assert elem_index(1, [2, 1]) == Just(1)


def find(f: Callable[[_A], bool], xs: Iterable[_A]) -> Maybe[_A]:
    for x in xs:
        if f(x):
            return Just(x)
    return Nothing()


def _test_find():
    assert find(lambda x: x == 1, []) == Nothing()
    assert find(lambda x: x == 1, [1]) == Just(1)
    assert find(lambda x: x == 1, [2]) == Nothing()
    assert find(lambda x: x == 1, [2, 1]) == Just(1)


def find_index(f: Callable[[_A], bool], xs: Iterable[_A]) -> Maybe[int]:
    for i, x in enumerate(xs):
        if f(x):
            return Just(i)
    return Nothing()


def _test_find_index():
    assert find_index(lambda x: x == 1, []) == Nothing()
    assert find_index(lambda x: x == 1, [1]) == Just(0)
    assert find_index(lambda x: x == 1, [2]) == Nothing()
    assert find_index(lambda x: x == 1, [2, 1]) == Just(1)


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


def _test_intersperse():
    assert intersperse(0, []) == []
    assert intersperse(0, [1]) == [1]
    assert intersperse(0, [1, 2]) == [1, 0, 2]
    assert intersperse(0, [1, 2, 3]) == [1, 0, 2, 0, 3]


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


def _test_intercalate():
    assert intercalate([], []) == []
    assert intercalate([], [[]]) == []
    assert intercalate([], [[1]]) == [1]
    assert intercalate([], [[1], [2]]) == [1, 2]
    assert intercalate([0], [[1], [2]]) == [1, 0, 2]
    assert intercalate([0, 0], [[1], [2]]) == [1, 0, 0, 2]


def transpose(xss: Iterable[Iterable[_A]]) -> Iterable[Iterable[_A]]:
    if not xss:
        return Seq(lambda: iter([]))
    else:
        return Seq(lambda: (list(row) for row in builtins.zip(*xss)))


def _test_transpose():
    assert transpose([]) == []
    assert transpose([[]]) == []
    assert transpose([[1]]) == [[1]]
    assert transpose([[1, 2]]) == [[1], [2]]
    assert transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]
    assert transpose([[1, 2], [3, 4], [5, 6]]) == [[1, 3, 5], [2, 4, 6]]


def unique(seq: Iterable[_A]) -> Iterable[_A]:
    def _unique(acc: Iterable[_A], x: _A) -> Iterable[_A]:
        if x not in acc:
            return append(acc, [x])
        return acc

    return foldl(_unique, [], seq)


def _test_unique():
    assert unique([]) == []
    assert unique([1]) == [1]
    assert unique([1, 1]) == [1]
    assert unique([1, 2]) == [1, 2]
    assert unique([1, 2, 1]) == [1, 2]


_Ord_A = TypeVar("_Ord_A", bound=Ord | int)
_Ord_B = TypeVar("_Ord_B", bound=Ord | int)


def sort(seq: Iterable[_Ord_A]) -> Iterable[_Ord_A]:
    return Seq.from_list(sorted(seq))


def _test_sort():
    assert sort([]) == []
    assert sort([3, 2, 1]) == [1, 2, 3]
    assert sort([3, 2, 1, 1, 2, 3]) == [1, 1, 2, 2, 3, 3]
    assert sort([1, 2, 3]) == [1, 2, 3]


def sort_on(f: Callable[[_A], _Ord_B], seq: Iterable[_A]) -> Iterable[_A]:
    return Seq.from_list(sorted(seq, key=f))


def _test_sort_on():
    assert sort_on(lambda x: x, []) == []
    assert sort_on(lambda x: x, [3, 2, 1]) == [1, 2, 3]
    assert sort_on(lambda x: x, [3, 2, 1, 1, 2, 3]) == [1, 1, 2, 2, 3, 3]
    assert sort_on(lambda x: x, [1, 2, 3]) == [1, 2, 3]
    assert sort_on(lambda x: -x, [1, 2, 3]) == [3, 2, 1]
    assert sort_on(lambda x: -x, [3, 2, 1, 1, 2, 3]) == [3, 3, 2, 2, 1, 1]


def is_prefix_of(xs: Iterable[_A], ys: Iterable[_A]) -> bool:
    if length(xs) > length(ys):
        return False
    else:
        return all(x == y for x, y in builtins.zip(xs, ys))


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
    if not xs:
        return True
    elif length(xs) > length(ys):
        return False
    else:
        xs_list = list(xs)
        ys_list = list(ys)
        return xs_list == ys_list[-len(xs_list) :]


def _test_is_suffix_of():
    assert is_suffix_of([], [])
    assert is_suffix_of([], [1])
    assert is_suffix_of([1], [1])
    assert is_suffix_of([1, 2], [1, 2])
    assert is_suffix_of([1, 2], [0, 1, 2])
    assert not is_suffix_of([1, 2], [1])
    assert not is_suffix_of([1, 2], [3, 1])
    assert not is_suffix_of([1, 2], [4, 3, 1])


# Other


# ! Side-effect
def for_each(f: Callable[[_A], None], xs: Iterable[_A]) -> None:
    for x in xs:
        f(x)


def if_else(cond: bool, t: _A, f: _A) -> _A:
    return t if cond else f


def body(*exps):
    return [exp for exp in exps][-1]
