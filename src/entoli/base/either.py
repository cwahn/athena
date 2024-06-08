from __future__ import annotations
from typing import TypeVar


_A = TypeVar("_A")
_B = TypeVar("_B")

type Either[_A, _B] = _A | _B
