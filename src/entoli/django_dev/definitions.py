from dataclasses import dataclass, field
from typing import Iterable, Protocol

from entoli.py_code.py_code import PyDependecy, PyIdent
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.map import Map
from entoli.py_code.py_code import IdEnv


@dataclass
class DjangoField(Protocol):
    def to_py_snippet(self, id_env: IdEnv, field_name) -> str: ...
    # def deps(self) -> Iterable[PyDependecy]: ...
    def deps(self) -> Map[str, PyDependecy]: ...


@dataclass
class BooleanField(DjangoField):
    null: bool = False
    mb_default: Maybe[bool] = field(default_factory=Nothing)
    blank: bool = False
    mb_verbose_name: Maybe[str] = field(default_factory=Nothing)
    mb_help_text: Maybe[str] = field(default_factory=Nothing)

    def to_py_snippet(self, id_env: IdEnv, field_name) -> str:
        return f"{self.deps()["BooleanField"].ident.inverse_name_env(id_env)}(null={self.null}, default={self.mb_default.unwrap() if self.mb_default else None}, blank={self.blank}, verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None}, help_text={self.mb_help_text.unwrap() if self.mb_help_text else '""'})"

    def deps(self) -> Map[str, PyDependecy]:
        return Map(
            [
                (
                    "BooleanField",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "db", "models"],
                            mb_name=Just("BooleanField"),
                        ),
                    ),
                )
            ]
        )
