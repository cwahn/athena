from __future__ import annotations
import builtins
from collections import deque
from dataclasses import dataclass
import operator
from typing import Callable, Generic, Iterable, Tuple, Type, TypeVar

from entoli.base.typeclass import _B, Monad
from entoli.data.seq import Seq
from entoli.prelude import (
    concat,
    map,
    append,
    concat_map,
    foldl,
    length,
    null,
    take_while,
    transpose,
)


_A = TypeVar("_A")
_B = TypeVar("_B")
_G = TypeVar("_G")


@dataclass
class Tree(Generic[_A], Monad[_A]):
    value: _A
    children: Iterable[Tree[_A]]

    def __repr__(self) -> str:
        if null(self.children):
            return f"Tree({self.value})"
        else:
            pre_ordered = self.level_appended().pre_order()
            return "\n".join(
                map(
                    lambda x: f"{'  ' * x[0]}{x[1]}",
                    pre_ordered,
                )
            )

    def fmap(self, f: Callable[[_A], _B]) -> Tree[_B]:
        return Tree(f(self.value), map(lambda t: t.fmap(f), self.children))

    @staticmethod
    def pure(x: _A) -> Tree[_A]:
        return Tree(x, [])

    def ap(self, f: Tree[Callable[[_A], _B]]) -> Tree[_B]:
        return Tree(
            f.value(self.value),
            append(
                map(
                    lambda x: x.fmap(f.value),
                    self.children,
                ),
                map(
                    lambda f_: self.ap(f_),
                    f.children,
                ),
            ),
        )

    def and_then(self, f: Callable[[_A], Tree[_B]]) -> Tree[_B]:
        new_tree = f(self.value)
        return Tree(
            new_tree.value,
            append(
                new_tree.children,
                map(lambda t: t.and_then(f), self.children),
            ),
        )

    @staticmethod
    def unfold(f: Callable[[_B], Tuple[_A, Iterable[_B]]], seed: _B) -> Tree[_A]:
        """
        Unfold a tree from a seed value.
        f should return a tuple of value and children.
        If f doesn't return empty iterable at leaf nodes, the tree will be infinite.
        """

        value, children = f(seed)

        return Tree(
            value,
            map(
                lambda x: Tree.unfold(f, x),
                children,
            ),
        )

    def fold(self, f: Callable[[_A, Iterable[_B]], _B]) -> _B:
        """
        Fold a tree using a function f.
        f should take a value and an iterable of results from folding children.
        """
        return f(
            self.value,
            map(
                lambda x: x.fold(f),
                self.children,
            ),
        )

    def flatten(self) -> Iterable[_A]:
        """
        Returns the elements of a tree in pre-order.
        """
        return append([self.value], concat_map(lambda x: x.flatten(), self.children))

    def levels(self) -> Iterable[Iterable[_A]]:
        """
        Return a sequence of values at each level of the tree.
        """

        return append(
            Seq.pure(Seq.pure(self.value)),
            map(
                lambda ass: concat(ass),
                transpose(map(lambda t: t.levels(), self.children)),
            ),
        )

    def height(self) -> int:
        if null(self.children):
            return 0
        else:
            return 1 + max(map(lambda t: t.height(), self.children))

    def level_appended(self, depth: int = 0) -> Tree[Tuple[int, _A]]:
        if null(self.children):
            return Tree((depth, self.value), [])
        else:
            return Tree(
                (depth, self.value),
                map(
                    lambda x: x.level_appended(depth + 1),
                    self.children,
                ),
            )

    def zip(self, other: Tree[_B]) -> Tree[Tuple[_A, _B]]:
        if null(self.children) or null(other.children):
            return Tree((self.value, other.value), [])
        else:
            if length(self.children) != length(other.children):
                raise ValueError("Trees must have the same shape")
            return Tree(
                value=(self.value, other.value),
                children=map(
                    lambda x: x[0].zip(x[1]),
                    builtins.zip(self.children, other.children),
                ),
            )

    def pre_order(self) -> Iterable[_A]:
        """Preorder traversal: Root -> Left -> Right"""
        return self.flatten()

    def post_order(self) -> Iterable[_A]:
        """Postorder traversal: Left -> Right -> Root"""
        return append(
            concat_map(lambda x: x.post_order(), self.children),
            [self.value],
        )

    def level_order(self) -> Iterable[_A]:
        """Level-order traversal"""

        def bfs(trees: Iterable[Tree[_A]]) -> Iterable[_A]:
            if null(trees):
                return []
            else:
                return append(
                    map(lambda x: x.value, trees),
                    bfs(concat_map(lambda x: x.children, trees)),
                )

        return bfs([self])

    def complete(
        self,
        to_group: Callable[[_A], _G],
        from_group: Callable[[_G], _A],
        unit: _G = 0,
    ) -> Tree[_A]:
        if null(self.children):
            return self
        else:
            sum_of_children = foldl(
                operator.add,
                unit,
                map(lambda x: to_group(x.value), self.children),
            )
            error = to_group(self.value) - sum_of_children

            return Tree(
                self.value,
                append(
                    map(
                        lambda x: x.complete(to_group, from_group, unit),
                        self.children,
                    ),
                    [Tree(from_group(error), [])],
                ),
            )


class _TestTree:
    def _test_unfold(self):
        def f(x: int) -> Tuple[bool, Iterable[int]]:
            if x >= 3:
                return (x % 2 == 0, [])
            else:
                return (x % 2 == 0, [x + 1, x + 2])

        assert Tree.unfold(f, 0) == Tree(
            True,  # 0
            [
                Tree(
                    False,  # 1
                    [
                        Tree(
                            True,  # 2
                            [
                                Tree(False, []),  # 3
                                Tree(True, []),  # 4
                            ],
                        ),
                        Tree(
                            False,  # 3
                            [],
                        ),
                    ],
                ),
                Tree(
                    True,  # 2
                    [
                        Tree(False, []),  # 3
                        Tree(True, []),  # 4
                    ],
                ),
            ],
        )

    def _test_fold(self):
        tree_0 = Tree(0, [])
        assert tree_0.fold(lambda x, cs: x + sum(cs)) == 0

        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])
        assert tree_1.fold(lambda x, cs: x + sum(cs)) == 6

    def _test_flatten(self):
        tree_0 = Tree(0, [])
        assert tree_0.flatten() == [0]

        tree_1 = Tree(1, [Tree(11, [Tree(111, []), Tree(112, [])]), Tree(12, [])])
        assert tree_1.flatten() == [1, 11, 111, 112, 12]

    def test_levels(self):
        tree_0 = Tree(0, [])
        assert tree_0.levels() == [[0]]

        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])
        assert tree_1.levels() == [[1], [2, 3]]

    def _test_height(self):
        tree_0 = Tree(0, [])
        assert tree_0.height() == 0

        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])
        assert tree_1.height() == 1

    def _test_fmap(self):
        tree_0 = Tree(0, [])
        assert tree_0.fmap(lambda x: x + 1) == Tree(1, [])

        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])
        assert tree_1.fmap(lambda x: x + 1) == Tree(2, [Tree(3, []), Tree(4, [])])

    def _test_pure(self):
        assert Tree.pure(1) == Tree(1, [])

    def _test_ap(self):
        tree_0 = Tree(0, [])
        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])

        fs = Tree(
            lambda x: x + 1, [Tree(lambda x: x * 2, []), Tree(lambda x: x * 3, [])]
        )

        assert tree_0.ap(fs) == Tree(1, [Tree(0, []), Tree(0, [])])
        assert tree_1.ap(fs) == Tree(
            2,
            [
                # Application of root function to children
                Tree(3, []),
                Tree(4, []),
                # Application of children functions to self
                Tree(2, [Tree(4, []), Tree(6, [])]),
                Tree(3, [Tree(6, []), Tree(9, [])]),
            ],
        )

    def _test_and_then(self):
        tree_0 = Tree(0, [])
        tree_1 = Tree(1, [Tree(2, []), Tree(3, [])])

        def f(x: int) -> Tree[int]:
            return Tree(x + 1, [Tree(x * 2, []), Tree(x * 3, [])])

        assert tree_0.and_then(f) == Tree(1, [Tree(0, []), Tree(0, [])])
        assert tree_1.and_then(f) == Tree(
            2,
            [
                # Children of application of f to root
                Tree(2, []),
                Tree(3, []),
                # application of f to children of self
                Tree(3, [Tree(4, []), Tree(6, [])]),
                Tree(4, [Tree(6, []), Tree(9, [])]),
            ],
        )

    def _test_zip(self):
        tree1 = Tree(1, [Tree(2, []), Tree(3, [])])
        tree2 = Tree(10, [Tree(20, []), Tree(30, [])])

        assert tree1.zip(tree2) == Tree(
            (1, 10),
            [
                Tree((2, 20), []),
                Tree((3, 30), []),  # type: ignore
            ],
        )


def unfold_tree(f: Callable[[_B], Tuple[_A, Iterable[_B]]], seed: _B) -> Tree[_A]:
    """
    Unfold a tree from a seed value.
    f should return a tuple of value and children.
    If f doesn't return empty iterable at leaf nodes, the tree will be infinite.
    """

    value, children = f(seed)

    return Tree(
        value,
        map(
            lambda x: unfold_tree(f, x),
            children,
        ),
    )


def _test_unfold_tree():
    def f(x: int) -> Tuple[bool, Iterable[int]]:
        if x >= 3:
            return (x % 2 == 0, [])
        else:
            return (x % 2 == 0, [x + 1, x + 2])

    assert unfold_tree(f, 0) == Tree(
        True,  # 0
        [
            Tree(
                False,  # 1
                [
                    Tree(
                        True,  # 2
                        [
                            Tree(False, []),  # 3
                            Tree(True, []),  # 4
                        ],
                    ),
                    Tree(
                        False,  # 3
                        [],
                    ),
                ],
            ),
            Tree(
                True,  # 2
                [
                    Tree(False, []),  # 3
                    Tree(True, []),  # 4
                ],
            ),
        ],
    )


# todo unfold_tree_m

# todo unfold_tree_bf


def fold_tree(
    f: Callable[[_A, Iterable[_B]], _B],
    tree: Tree[_A],
) -> _B:
    """
    Fold a tree using a function f.
    f should take a value and an iterable of results from folding children.
    """
    return f(
        tree.value,
        map(
            lambda x: fold_tree(f, x),
            tree.children,
        ),
    )


def _test_fold_tree():
    tree_0 = Tree(0, [])
    assert fold_tree(lambda x, cs: x + sum(cs), tree_0) == 0

    tree1 = Tree(1, [Tree(2, []), Tree(3, [])])
    assert fold_tree(lambda x, cs: x + sum(cs), tree1) == 6


def merge_trees(trees: Iterable[Tree[_A]]) -> Tree[Iterable[_A]]:
    """
    Takes an iterable of trees and merges them into a single tree of iterable of values.
    Trees must be non-empty and have the same shape.
    """
    if not trees:
        raise ValueError("No trees to merge")

    root_values = map(lambda x: x.value, trees)

    if all(map(lambda t: null(t.children), trees)):  # If all trees are leaf nodes
        return Tree(root_values, [])
    else:
        merged_children = builtins.zip(*(tree.children for tree in trees))

        children = map(merge_trees, merged_children)

        return Tree(root_values, children)


def _test_merge_trees():
    tree1 = Tree(1, [Tree(2, []), Tree(3, [])])

    tree2 = Tree(4, [Tree(5, []), Tree(6, [])])

    merged_tree = merge_trees([tree1, tree2])

    assert merged_tree == Tree(
        [1, 4],
        [
            Tree([2, 5], []),
            Tree([3, 6], []),
        ],
    )
