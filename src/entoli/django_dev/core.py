from __future__ import annotations

from pathlib import Path
from pickletools import read_uint1
from typing import Iterable, List, Protocol, Dict

from dataclasses import dataclass
from xmlrpc.client import Boolean
from entoli.base.io import Io
from entoli.base.maybe import Maybe, Nothing
from entoli.django_dev.py_code import PyCode, PyIdent, write_py_code
from entoli.prelude import concat, foldl, intercalate, map
from entoli.system import append_file, read_file


# Prerequsites: In venv with Django installed, run the following commands:
# A definition will result list of pycodes which will be added to the graph


@dataclass
class DjangoField(Protocol):
    def to_py_snippet(self) -> str: ...

    def strict_deps(self) -> Iterable[PyIdent]: ...

    def weak_deps(self) -> Iterable[PyIdent]: ...


@dataclass
class BooleanField(DjangoField):
    null: bool = False
    default: bool = False
    blank: bool = False
    mb_verbose_name: Maybe[str] = Nothing()
    mb_help_text: Maybe[str] = Nothing()

    def to_py_snippet(self) -> str:
        return f"BooleanField(null={self.null}, default={self.default}, blank={self.blank}, verbose_name={self.mb_verbose_name}, help_text={self.mb_help_text})"

    def strict_deps(self) -> Iterable[PyIdent]:
        return [PyIdent(module=["django", "db", "models"], qual_name=["BooleanField"])]

    def weak_deps(self) -> Iterable[PyIdent]:
        return []


@dataclass
class CharField(DjangoField):
    max_length: int
    null: bool = False
    default: bool = False
    blank: bool = False
    mb_verbose_name: Maybe[str] = Nothing()
    mb_help_text: Maybe[str] = Nothing()

    def to_py_snippet(self) -> str:
        return f"CharField(max_length={self.max_length}, null={self.null}, default={self.default}, blank={self.blank}, verbose_name={self.mb_verbose_name}, help_text={self.mb_help_text})"

    def strict_deps(self) -> Iterable[PyIdent]:
        return [PyIdent(module=["django", "db", "models"], qual_name=["CharField"])]

    def weak_deps(self) -> Iterable[PyIdent]:
        return []


@dataclass
class DjangoModel:
    name: str
    fields: Dict[str, DjangoField]

    def to_py_codes(self, project_name: str, app_name: str) -> Iterable[PyCode]:
        definition = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "models"], qual_name=[self.name]
            ),
            code=lambda path: append_file(
                path,
                "\n".join(
                    [
                        f"\n\nclass {self.name}(models.Model):",
                        *[
                            f"    {field_name} = {field.to_py_snippet()}"
                            for field_name, field in self.fields.items()
                        ],
                    ]
                ),
            ),
            strict_deps=concat(map(lambda f: f.strict_deps(), self.fields.values())),
            weak_deps=concat(map(lambda f: f.weak_deps(), self.fields.values())),
        )

        model_form_class = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "forms"],
                qual_name=[f"{self.name}Form"],
            ),
            code=lambda path: append_file(
                path,
                "\n".join(
                    [
                        f"\n\nclass {self.name}Form(forms.ModelForm):",
                        "    class Meta:",
                        f"        model = {self.name}",
                        "        fields = '__all__'",
                    ]
                ),
            ),
            strict_deps=[
                PyIdent(module=["django", "forms", "models"], qual_name=["ModelForm"]),
                PyIdent(
                    module=[project_name, app_name, "models"], qual_name=[self.name]
                ),
            ],
            weak_deps=[],
        )

        admin_add = PyCode(
            ident=PyIdent(module=[project_name, app_name, "admin"], qual_name=[]),
            code=lambda path: append_file(
                path,
                f"\n\nadmin.site.register({self.name})",
            ),
            strict_deps=[
                PyIdent(
                    module=["django", "contrib"],
                    qual_name=["admin"],
                ),
                PyIdent(
                    module=[project_name, app_name, "models"], qual_name=[self.name]
                ),
            ],
            weak_deps=[],
        )

        # todo serializer

        return [definition, model_form_class, admin_add]


@dataclass
class DjangoApp:
    name_slug: str
    models: Iterable[DjangoModel]

    def to_py_codes(self, project_name: str) -> Iterable[PyCode]:
        model_codes = concat(
            map(lambda m: m.to_py_codes(project_name, self.name_slug), self.models)
        )

        add_apps_to_settings = PyCode(
            ident=PyIdent(module=[project_name, "settings"], qual_name=[]),
            # todo Futher refinement for substitution logic
            code=lambda path: append_file(
                path,
                f"\n\nINSTALLED_APPS += ['{self.name_slug}']",
            ),
            strict_deps=[],
            weak_deps=[],
        )

        add_app_urls_to_project = PyCode(
            ident=PyIdent(module=[project_name, "urls"], qual_name=[]),
            code=lambda path: append_file(
                path,
                f"\n\nurlpatterns += [path('{self.name_slug}/', include('{self.name_slug}.urls'))]",
            ),
            strict_deps=[
                PyIdent(module=["django", "urls", "conf"], qual_name=["include"]),
            ],
            weak_deps=[],
        )

        return [add_apps_to_settings, add_app_urls_to_project, *model_codes]


@dataclass
class DjangoProject:
    name: str
    apps: Iterable[DjangoApp]

    def to_py_codes(self) -> Iterable[PyCode]:
        app_codes = concat(map(lambda a: a.to_py_codes(self.name), self.apps))

        return app_codes

    def write(self) -> Io[None]:
        return foldl(
            lambda acc, code: acc.then(write_py_code(code)),
            Io.pure(None),
            self.to_py_codes(),
        )
