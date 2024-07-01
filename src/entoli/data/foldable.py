from typing import Callable, List, Protocol, TypeVar


_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)

_A = TypeVar("_A")
_B = TypeVar("_B")


class FoldableBase(Protocol[_A_co]):
    def foldr(self, f: Callable[[_A_co, _B], _B], z: _B) -> _B: ...
    def foldl(self, f: Callable[[_B, _A_co], _B], z: _B) -> _B: ...
    def fold_map(self, f: Callable[[_A_co], _B]) -> _B: ...


class Foldable(FoldableBase[_A], Protocol[_A]):
    def to_list(self) -> List[_A]:
        return self.foldr(lambda x, xs: [x] + xs, [])

    def null(self) -> bool:
        return self.foldr(lambda _0, _1: False, True)

    def length(self) -> int:
        return self.foldl(lambda acc, _0: acc + 1, 0)

    def elem(self, x: _A) -> bool:
        return self.foldr(lambda y, acc: acc or y == x, False)

    # def sum(self) -> Monoid:
    #     return self.fold_map(lambda x: x, Monoid.mempty())

    # def product(self) -> Monoid:
    #     return self.fold_map(lambda x: x, Monoid.mempty())
