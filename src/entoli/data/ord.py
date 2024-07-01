from __future__ import annotations
from typing import Any, Protocol


class Ord(Protocol):
    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...
