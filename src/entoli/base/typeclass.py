from __future__ import annotations
from typing import Any, Callable, List, Protocol, Type, TypeVar


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


class Ord(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


class Show(Protocol):
    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...


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
