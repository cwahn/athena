from __future__ import annotations
from typing import Protocol, Self, TypeVar

from entoli.data.applicative import Applicative


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


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
