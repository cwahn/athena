from __future__ import annotations
import builtins
from collections import deque
from dataclasses import dataclass
import operator
from typing import Callable, Generic, Iterable, Tuple, Type, TypeVar

from entoli.prelude import map, append, concat_map, foldl, length, null


_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass
class Tree(Generic[_A]):
    value: _A
    children: Iterable[Tree[_A]]

    def __repr__(self) -> str:
        if null(self.children):
            return f"Tree({self.value})"
        else:
            pre_ordered = self.depth_appended().preorder()
            return "\n".join(
                map(
                    lambda x: f"{'  ' * x[0]}{x[1]}",
                    pre_ordered,
                )
            )

    # @staticmethod
    # def build(value: _A, get_children: Callable[[_A], Iterable[_A]]) -> Tree[_A]:
    #     """
    #     get_children should return empty iterable at leaf nodes.
    #     Otherwise, it should return iterable of children nodes.
    #     """
    #     if null(get_children(value)):
    #         return Tree(value, [])
    #     else:
    #         return Tree(
    #             value,
    #             map(
    #                 lambda x: Tree.build(x, get_children),
    #                 get_children(value),
    #             ),
    #         )

    # def flatten(self) -> Iterable[_A]:
    #     # yield self.value
    #     # for child in self.children:
    #     #     yield from child.flatten()
    #     return append([self.value], concat_map(lambda x: x.flatten(), self.children))

    # def depth(self) -> int:
    #     if null(self.children):
    #         return 1
    #     else:
    #         return 1 + max(map(lambda x: x.depth(), self.children))

    # def fmap(self, f: Callable[[_A], _B]) -> Tree[_B]:
    #     # ! Can't mutate tree with lazy value
    #     return Tree(f(self.value), map(lambda x: x.fmap(f), self.children))

    # def zip(self, other: Tree[_B]) -> Tree[Tuple[_A, _B]]:
    #     if null(self.children) or null(other.children):
    #         return Tree((self.value, other.value), [])
    #     else:
    #         if length(self.children) != length(other.children):
    #             raise ValueError("Trees must have the same shape")
    #         return Tree(
    #             value=(self.value, other.value),
    #             children=map(
    #                 lambda x: x[0].zip(x[1]),
    #                 zip(self.children, other.children),
    #             ),
    #         )

    def depth_appended(self, depth: int = 0) -> Tree[Tuple[int, _A]]:
        if null(self.children):
            return Tree((depth, self.value), [])
        else:
            return Tree(
                (depth, self.value),
                map(
                    lambda x: x.depth_appended(depth + 1),
                    self.children,
                ),
            )

    # # todo Support general monoid
    # # def complete(
    # #     self, to_monoid: Callable[[_A], int], from_monoid: Callable[[int], _A]
    # # ) -> Tree[_A]:
    # #     if null(self.children):
    # #         return self
    # #     else:
    # #         sum_of_children = sum(map(lambda x: to_monoid(x.value), self.children))
    # #         delta = to_monoid(self.value) - sum_of_children

    # #         error_value = from_monoid(delta)

    # #         return Tree(
    # #             self.value,
    # #             append(
    # #                 map(
    # #                     lambda x: x.complete(to_monoid, from_monoid),
    # #                     self.children,
    # #                 ),
    # #                 [Tree(error_value, [])],
    # #             ),
    # #         )

    # _M = TypeVar("_M")

    # # ? Actually a group
    # def complete(
    #     self,
    #     to_monoid: Callable[[_A], _M],
    #     from_monoid: Callable[[_M], _A],
    #     monoid_zero: _M = 0,
    # ) -> Tree[_A]:
    #     if null(self.children):
    #         return self
    #     else:
    #         # sum_of_children = sum(map(lambda x: to_monoid(x.value), self.children))
    #         sum_of_children = foldl(
    #             operator.add,
    #             monoid_zero,
    #             map(lambda x: to_monoid(x.value), self.children),
    #         )
    #         delta = to_monoid(self.value) - sum_of_children

    #         error_value = from_monoid(delta)

    #         return Tree(
    #             self.value,
    #             # ! Can't mutate tree with lazy value
    #             append(
    #                 map(
    #                     lambda x: x.complete(to_monoid, from_monoid, monoid_zero),
    #                     self.children,
    #                 ),
    #                 [Tree(error_value, [])],
    #             ),
    #         )

    def preorder(self) -> Iterable[_A]:
        """Preorder traversal: Root -> Left -> Right"""
        result = []
        result.append(self.value)
        for child in self.children:
            result.extend(child.preorder())
        return result

    # def inorder(self) -> Iterable[_A]:
    #     """Inorder traversal: Left -> Root -> Right"""
    #     # Assuming binary tree structure for inorder traversal
    #     result = []
    #     children = list(self.children)
    #     if children:
    #         result.extend(children[0].inorder())
    #     result.append(self.value)
    #     if len(children) > 1:
    #         result.extend(children[1].inorder())
    #     return result

    # def postorder(self) -> Iterable[_A]:
    #     """Postorder traversal: Left -> Right -> Root"""
    #     # result = []
    #     # for child in self.children:
    #     #     result.extend(child.postorder())
    #     # result.append(self.value)
    #     # return result

    #     if null(self.children):
    #         return [self.value]
    #     else:
    #         children_part = concat_map(lambda x: x.postorder(), self.children)
    #         return append(children_part, [self.value])

    # def level_order(self) -> Iterable[_A]:
    #     """Level-order traversal: Breadth-First Search"""
    #     result = []
    #     queue = deque([self])
    #     while queue:
    #         node = queue.popleft()
    #         result.append(node.value)
    #         queue.extend(node.children)  # type: ignore
    #     return result


# class _TestTree:
# def _test_build(self):
#     def get_children(x):
#         if x == 1:
#             return [2, 3, 4]
#         else:
#             return []

#     tree = Tree.build(1, get_children)
#     assert tree.value == 1
#     children = list(tree.children)

#     assert children[0].value == 2
#     assert children[1].value == 3
#     assert children[2].value == 4

#     assert tree.children == [
#         Tree(2, []),
#         Tree(3, []),
#         Tree(4, []),
#     ]

# def _test_preorder(self):
#     tree = Tree(1, [Tree(11, [Tree(111, []), Tree(112, [])]), Tree(12, [])])
#     assert tree.preorder() == [1, 11, 111, 112, 12]

# def _test_zip(self):
#     tree1: Tree[int] = Tree(
#         1, [Tree(11, [Tree(111, []), Tree(112, [])]), Tree(12, [])]
#     )
#     tree2: Tree[int] = Tree(
#         10, [Tree(101, [Tree(1011, []), Tree(1012, [])]), Tree(102, [])]
#     )

#     zipped_tree = tree1.zip(tree2)

#     assert zipped_tree == Tree(
#         (1, 10),
#         [
#             Tree((11, 101), [Tree((111, 1011), []), Tree((112, 1012), [])]),  # type: ignore
#             Tree((12, 102), []),
#         ],  # type: ignore
#     )


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
