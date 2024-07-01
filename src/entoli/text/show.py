from __future__ import annotations
from typing import Protocol


class Show(Protocol):
    def __repr__(self) -> str: ...

    def __str__(self) -> str: ...
