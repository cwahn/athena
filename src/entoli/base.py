from __future__ import annotations
from re import M
from typing import Any, Callable, Iterable, List, Protocol, Self, Type, TypeVar


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Functor(Protocol[_A_co]):
    # fmap :: Functor f => (a -> b) -> f a -> f b
    def fmap(self, f: Callable[[_A], _B]) -> Functor[_B]: ...


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    # ap :: Applicative f => f (a -> b) -> f a -> f b
    def ap(self, f: Any[Callable[[_A_co], Any]]) -> Applicative[Any]: ...


_MB = TypeVar("_MB", bound="Monad")


class Monad(Applicative[_A_co], Protocol[_A_co]):
    # m a -> (a -> m b) -> m b
    def and_then(self, f: Callable[[_A], Any[_B]]) -> Monad[Any]: ...

    # ! Can't express with current type system
    # def then(self, x: Any[_B]) -> Monad[_B]:
    #     return self.and_then(lambda _: x)


class Alternative(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def empty() -> Alternative[_A_co]: ...

    def or_else(self, other: Self) -> Self: ...

    # ! Can't express with current type system

    # # some v = (:) <$> v <*> many v
    # def some(self) -> Alternative[Iterable[_A_co]]:
    #     return Applicative.ap(
    #         Applicative.fmap(lambda x: lambda xs: [x] + xs, self), self.many()
    #     )

    # # many v = some v <|> pure []
    # def many(self) -> Alternative[Iterable[_A_co]]:
    #     return self.some().or_else(Alternative[Iterable[_A_co]].pure([]))


class MonadPlus(Monad[_A_co], Protocol[_A_co]):
    @staticmethod
    def mzero() -> MonadPlus[_A_co]: ...

    def mplus(self, other: Self) -> Self: ...


class Foldable(Protocol[_A_co]):
    def foldr(self, f: Callable[[_A_co, _B], _B], z: _B) -> _B: ...

    def foldl(self, f: Callable[[_B, _A_co], _B], z: _B) -> _B: ...

    def fold_map(self, f: Callable[[_A_co], _B], z: Type[_B]) -> _B: ...


class Traversable(Functor[_A_co], Foldable[_A_co], Protocol[_A_co]):
    def traverse(self, f: Callable[[_A_co], _B], t: Type[_B]) -> _B: ...

    def sequence(self, t: Type[_A_co]) -> _A_co: ...


class Ord(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


class Show(Protocol):
    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...


class ToBool(Protocol):
    def __bool__(self) -> bool: ...
