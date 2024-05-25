from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Protocol, List

from entoli.prelude import concat, filter_map, map, unlines
from entoli.py_code.py_code import (
    PyCode,
    PyDependecy,
    PyIdent,
    ReferEnv,
    write_codes,
)
from entoli.base.maybe import Just, Maybe, Nothing
from entoli.map import Map
from entoli.py_code.py_code import IdEnv


@dataclass
class DjangoField(Protocol):
    def to_py_snippet(self, refer: ReferEnv, field_name) -> str: ...
    # def deps(self) -> Iterable[PyDependecy]: ...
    def deps(self) -> Map[str, PyDependecy]: ...


@dataclass
class BooleanField(DjangoField):
    null: bool = False
    mb_default: Maybe[bool] = field(default_factory=Nothing)
    blank: bool = False
    mb_verbose_name: Maybe[str] = field(default_factory=Nothing)
    mb_help_text: Maybe[str] = field(default_factory=Nothing)

    def to_py_snippet(self, refer: ReferEnv, field_name) -> str:
        return unlines(
            [
                f"{refer('BooleanField')}(null={self.null},",
                f"    default={self.mb_default.unwrap() if self.mb_default else None},",
                f"    blank={self.blank},",
                f"    verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None},",
                f"    help_text={self.mb_help_text.unwrap() if self.mb_help_text else '""'})",
            ]
        )

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


@dataclass
class CharField(DjangoField):
    max_length: int
    null: bool = False
    mb_default: Maybe[str] = field(default_factory=Nothing)
    blank: bool = False
    mb_verbose_name: Maybe[str] = field(default_factory=Nothing)
    mb_help_text: Maybe[str] = field(default_factory=Nothing)

    def to_py_snippet(self, refer: ReferEnv, field_name) -> str:
        return unlines(
            [
                f"{refer('CharField')}(max_length={self.max_length},",
                f"    null={self.null},",
                f"    default={self.mb_default.unwrap() if self.mb_default else None},",
                f"    blank={self.blank},",
                f"    verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None},",
                f"    help_text={self.mb_help_text.unwrap() if self.mb_help_text else '""'})",
            ]
        )

    def deps(self) -> Map[str, PyDependecy]:
        return Map(
            [
                (
                    "CharField",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "db", "models"],
                            mb_name=Just("CharField"),
                        ),
                    ),
                )
            ]
        )


@dataclass
class DjangoModel:
    name: str
    fields: Map[str, DjangoField]

    def deps(self) -> Map[str, PyDependecy]:
        return Map(
            [
                (
                    "django_model",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "db", "models"], mb_name=Nothing()
                        )
                    ),
                ),
            ]
        )

    def to_py_codes(self, project_name: str, app_name: str) -> Iterable[PyCode]:
        definition_deps = Map(
            [
                (
                    "django_model",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "db", "models"], mb_name=Nothing()
                        )
                    ),
                ),
            ]
        )

        def _definition_code(refer: ReferEnv, imported_content) -> str:
            def_lines = unlines(
                [
                    f"class {self.name}({refer('django_model')}.Model):",
                    *[
                        f"    {field_name}: {field.to_py_snippet(refer, field_name)}"
                        for field_name, field in self.fields.items()
                    ],
                ]
            )

            return f"{imported_content}\n{def_lines}"

        definition = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "models"],
                mb_name=Just(self.name),
            ),
            code=_definition_code,
            deps=definition_deps,
        )

        model_from_deps = Map(
            [
                (
                    "django_forms",
                    PyDependecy(
                        ident=PyIdent(module=["django", "forms"], mb_name=Nothing()),
                    ),
                ),
                (
                    "self_model",
                    PyDependecy(
                        ident=PyIdent(
                            module=[project_name, app_name, "models"],
                            mb_name=Just(self.name),
                        )
                    ),
                ),
            ]
        )

        def _model_form_code(refer: ReferEnv, imported_content: str) -> str:
            model_form_lines = unlines(
                [
                    f"class {self.name}Form({refer('django_form')}.ModelForm):",
                    "    class Meta:",
                    f"        model = {refer('self_model')}",
                    "        fields = '__all__'",
                ]
            )

            return f"{imported_content}\n{model_form_lines}"

        model_form = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "forms"],
                mb_name=Just(f"{self.name}Form"),
            ),
            code=_model_form_code,
            deps=model_from_deps,
        )

        admin_deps = Map(
            [
                (
                    "admin",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "contrib", "admin"], mb_name=Nothing()
                        )
                    ),
                ),
                (
                    "self_model",
                    PyDependecy(
                        ident=PyIdent(
                            module=[project_name, app_name, "models"],
                            mb_name=Just(self.name),
                        )
                    ),
                ),
            ]
        )

        def _admin_code(refer: ReferEnv, imported_content: str) -> str:
            admin_lines = unlines(
                [
                    f"{refer('admin')}.site.register({refer('self_model')})",
                ]
            )

            return f"{imported_content}\n{admin_lines}"

        admin = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "admin"],
                mb_name=Just("admin"),
            ),
            code=_admin_code,
            deps=admin_deps,
        )

        return [definition, model_form, admin]


@dataclass
class DjangoApp:
    name: str
    models: Map[str, DjangoModel]

    def to_py_codes(self, project_name: str) -> Iterable[PyCode]:
        installed_apps_deps = Map([])

        def _installed_apps_code(refer: ReferEnv, imported_content: str) -> str:
            installed_apps_lines = f"INSTALLED_APPS += ['{self.name}']"

            return f"{imported_content}\n{installed_apps_lines}"

        installed_apps = PyCode(
            ident=PyIdent(
                module=[project_name],
                mb_name=Just("settings"),
            ),
            code=_installed_apps_code,
            deps=installed_apps_deps,
        )

        add_to_project_urls_deps = Map(
            [
                (
                    "path",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "urls"],
                            mb_name=Just("path"),
                        ),
                    ),
                ),
                (
                    "include",
                    PyDependecy(
                        ident=PyIdent(
                            module=["django", "urls"],
                            mb_name=Just("include"),
                        ),
                    ),
                ),
                (
                    "self_urls",
                    PyDependecy(
                        ident=PyIdent(
                            module=[project_name, self.name, "urls"],
                            mb_name=Nothing(),
                        ),
                    ),
                ),
            ]
        )

        def _add_to_project_urls_code(refer: ReferEnv, imported_content: str) -> str:
            add_to_project_urls_lines = unlines(
                [
                    f"path('{self.name}/', include('{refer('self_urls')}')),",
                ]
            )

            return f"{imported_content}\n{add_to_project_urls_lines}"

        add_to_project_urls = PyCode(
            ident=PyIdent(
                module=[project_name, "urls"],
                mb_name=Just("urlpatterns"),
            ),
            code=_add_to_project_urls_code,
            deps=add_to_project_urls_deps,
        )

        model_codes = concat(
            map(
                lambda model: model.to_py_codes(project_name, self.name),
                self.models.values(),
            )
        )

        return [installed_apps, add_to_project_urls, *model_codes]


@dataclass
class DjangoProject:
    name: str
    apps: List[DjangoApp]

    def to_py_codes(self) -> Iterable[PyCode]:
        model_codes = concat(
            map(
                lambda app: app.to_py_codes(self.name),
                self.apps,
            )
        )

        return model_codes

    def write(self, dir_path: Path):
        codes = self.to_py_codes()

        return write_codes(dir_path, codes)
