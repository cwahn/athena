from __future__ import annotations
from typing import Any, Callable, Iterable, List, Protocol, Self, Type, TypeVar


_A = TypeVar("_A")
_B = TypeVar("_B")

_A_co = TypeVar("_A_co", covariant=True)
_B_co = TypeVar("_B_co", covariant=True)


class Functor(Protocol[_A_co]):
    @staticmethod
    def fmap(f: Callable[[_A], _B], x: Any[_A_co]) -> Any[_B]: ...


class Applicative(Functor[_A_co], Protocol[_A_co]):
    @staticmethod
    def pure(x: Any) -> Any[_A]: ...

    @staticmethod
    def ap(f: Any[Callable[[_A], _B]], x: Any[_A]) -> Any[_B]: ...  # type: ignore


class Monad(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def bind(x: Any[_A], f: Callable[[_A], Any[_B]]) -> Any[_B]: ...

    # m a -> (a -> m b) -> m b


class Alternative(Applicative[_A_co], Protocol[_A_co]):
    @staticmethod
    def empty() -> Alternative[_A_co]: ...

    def or_else(self, other: Self) -> Self: ...

    # ! Hard to express with current type system

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


class Ord(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


class Show(Protocol):
    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...


class ToBool(Protocol):
    def __bool__(self) -> bool: ...


# Monkey-patch implementations


# @runtime_checkable
# class DuckLike(Protocol):
#     def quack(self) -> None: ...


# class Dog:
#     def bark(self) -> None:
#         print("Woof")


# def impl_duck(cls: Type) -> None:
#     cls.quack = lambda self: print("Quack")


# def add_protocol(cls: Type) -> Type:
#     impl_duck(cls)
#     return type(cls.__name__, (cls, DuckLike), {})


# def open(cls):
#     def update(extension):
#         for k, v in extension.__dict__.items():
#             if k != "__dict__":
#                 setattr(cls, k, v)
#         return cls

#     return update


# def act_like_duck(duck: DuckLike) -> None:
#     duck.quack()


# # Does raise an error
# # take_duck(Dog())

# Dog = add_protocol(Dog)

# act_like_duck(Dog())


# # make_list = lambda: [1, 2, 3]
# def make_list() -> List[int]:
#     return [1, 2, 3]


# # Does not raise an error
# # quack(list())

# # list = add_protocol(list)

# # @open(list)
# # class list:
# #     def quack(self) -> None:
# #         print("Quack")


# def quack(self) -> None:
#     print("Quacking")


# def list_fmap(f: Callable[[_A], _B], xs: List[_A]) -> List[_B]:
#     return [f(x) for x in xs]


# from forbiddenfruit import curse

# curse(list, "quack", quack)
# curse(list, "fmap", list_fmap)

# list.quack = quack

# a = [1, 2, 3]
# a.quack()

# # act_like_duck(list())

# # some_dict = {"a": 1, "b": 2}
# # quack(make_list())
