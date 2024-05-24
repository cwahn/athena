from __future__ import annotations

from pathlib import Path

from typing import Callable, Iterable, List, Protocol, Dict

from dataclasses import dataclass, field
from xmlrpc.client import Boolean
from entoli.base.io import Io
from entoli.base.maybe import Maybe, Nothing
from entoli.django_dev.py_code import PyCode, PyDependecy, PyIdent, write_py_code
from entoli.prelude import concat, foldl, intercalate, map
from entoli.system import append_file, read_file


# Prerequsites: In venv with Django installed, run the following commands:
# A definition will result list of pycodes which will be added to the graph


@dataclass
class DjangoField(Protocol):
    def to_py_snippet(self, dep_env: Callable[[str], str], field_name: str) -> str: ...

    # def strict_deps(self) -> Iterable[PyIdent]: ...

    # def weak_deps(self) -> Iterable[PyIdent]: ...

    def deps(self) -> Dict[str, PyDependecy]: ...


@dataclass
class BooleanField(DjangoField):
    null: bool = False
    mb_default: Maybe[bool] = field(default_factory=lambda: Nothing())
    blank: bool = False
    mb_verbose_name: Maybe[str] = field(default_factory=lambda: Nothing())
    mb_help_text: Maybe[str] = field(default_factory=lambda: Nothing())

    def to_py_snippet(self, dep_env: Callable[[str], str], field_name: str) -> str:
        return f"{dep_env(f"{field_name}::BooleanField")}(null={self.null}, default={self.mb_default.unwrap() if self.mb_default else None}, blank={self.blank}, verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None}, help_text={self.mb_help_text.unwrap() if self.mb_help_text else '""'})"

    # def strict_deps(self) -> Iterable[PyIdent]:
    #     return [PyIdent(module=["django", "db", "models"], qual_name=[])]

    # def weak_deps(self) -> Iterable[PyIdent]:
    #     return []

    def deps(self) -> Dict[str, PyDependecy]:
        return {
            "BooleanField": PyDependecy(
                ident=PyIdent(
                    module=["django", "db", "models"], qual_name=["BooleanField"]
                ),
                prefered_last_n=2,
            )
        }


@dataclass
class CharField(DjangoField):
    max_length: int
    null: bool = False
    mb_default: Maybe[str] = field(default_factory=lambda: Nothing())
    blank: bool = False
    mb_verbose_name: Maybe[str] = field(default_factory=lambda: Nothing())
    mb_help_text: Maybe[str] = field(default_factory=lambda: Nothing())

    # def to_py_snippet(self) -> str:
    #     return f"models.CharField(max_length={self.max_length}, null={self.null}, default={self.default}, blank={self.blank}, verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None}, help_text={self.mb_help_text.unwrap() if self.mb_help_text else None})"

    # def strict_deps(self) -> Iterable[PyIdent]:
    #     return [PyIdent(module=["django", "db", "models"], qual_name=[])]

    # def weak_deps(self) -> Iterable[PyIdent]:
    #     return []

    def to_py_snippet(self, dep_env: Callable[[str], str], field_name: str) -> str:
        return f"{dep_env(f'{field_name}::CharField')}(max_length={self.max_length}, null={self.null}, default={self.mb_default.unwrap() if self.mb_default else None}, blank={self.blank}, verbose_name={self.mb_verbose_name.unwrap() if self.mb_verbose_name else None}, help_text={self.mb_help_text.unwrap() if self.mb_help_text else '""'})"

    def deps(self) -> Dict[str, PyDependecy]:
        return {
            "CharField": PyDependecy(
                ident=PyIdent(
                    module=["django", "db", "models"], qual_name=["CharField"]
                ),
                prefered_last_n=2,
            )
        }


def mangled_dict_flatten(
    nested_dict: Dict[str, Dict[str, PyDependecy]],
) -> Dict[str, PyDependecy]:
    # Flatten with :: as separator
    return {f"{k}::{kk}": vv for k, v in nested_dict.items() for kk, vv in v.items()}


def sub_dict(
    mangled_dict: Dict[str, PyDependecy], prefix: str
) -> Dict[str, PyDependecy]:
    # Remove prefix and :: if starts with prefix
    return {
        k[len(prefix) + 2 :]: v for k, v in mangled_dict.items() if k.startswith(prefix)
    }


@dataclass
class DjangoModel:
    name: str
    fields: Dict[str, DjangoField]

    def to_py_codes(self, project_name: str, app_name: str) -> Iterable[PyCode]:
        definition = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "models"], qual_name=[self.name]
            ),
            # code=lambda path: append_file(
            #     path,
            #     "\n".join(
            #         [
            #             f"\nclass {self.name}(models.Model):",
            #             *[
            #                 f"    {field_name} = {field.to_py_snippet()}"
            #                 for field_name, field in self.fields.items()
            #             ],
            #         ]
            #     ),
            # ),
            code=lambda content, env: content
            + "\n"
            + "\n".join(
                [
                    f"\nclass {self.name}(models.Model):",
                    *[
                        f"    {field_name} = {field.to_py_snippet(env, field_name)}"
                        for field_name, field in self.fields.items()
                    ],
                ]
            ),
            # strict_deps=concat(map(lambda f: f.strict_deps(), self.fields.values())),
            # weak_deps=concat(map(lambda f: f.weak_deps(), self.fields.values())),
            deps=mangled_dict_flatten({k: v.deps() for k, v in self.fields.items()}),
        )

        # model_form_class = PyCode(
        #     ident=PyIdent(
        #         module=[project_name, app_name, "forms"],
        #         qual_name=[f"{self.name}Form"],
        #     ),
        #     code=lambda path: append_file(
        #         path,
        #         "\n".join(
        #             [
        #                 f"\nclass {self.name}Form(forms.ModelForm):",
        #                 "    class Meta:",
        #                 f"        model = {self.name}",
        #                 "        fields = '__all__'",
        #             ]
        #         ),
        #     ),
        #     strict_deps=[
        #         PyIdent(module=["django", "forms"], qual_name=[]),
        #         PyIdent(
        #             module=[project_name, app_name, "models"], qual_name=[self.name]
        #         ),
        #     ],
        #     weak_deps=[],
        # )

        model_form_class = PyCode(
            ident=PyIdent(
                module=[project_name, app_name, "forms"],
                qual_name=[f"{self.name}Form"],
            ),
            code=lambda content, env: content
            + "\n"
            + "\n".join(
                [
                    f"\nclass {self.name}Form(forms.ModelForm):",
                    "    class Meta:",
                    f"        model = {self.name}",
                    "        fields = '__all__'",
                ]
            ),
            deps={
                "forms::ModelForm": PyDependecy(
                    ident=PyIdent(module=["django", "forms"], qual_name=["ModelForm"]),
                ),
                f"{self.name}": PyDependecy(
                    ident=PyIdent(
                        module=[project_name, app_name, "models"], qual_name=[self.name]
                    ),
                ),
            },
        )

        # admin_add = PyCode(
        #     ident=PyIdent(module=[project_name, app_name, "admin"], qual_name=[]),
        #     code=lambda path: append_file(
        #         path,
        #         f"\nadmin.site.register({self.name})",
        #     ),
        #     strict_deps=[
        #         PyIdent(
        #             module=["django", "contrib"],
        #             qual_name=["admin"],
        #         ),
        #         PyIdent(
        #             module=[project_name, app_name, "models"], qual_name=[self.name]
        #         ),
        #     ],
        #     weak_deps=[],
        # )

        admin_add = PyCode(
            ident=PyIdent(module=[project_name, app_name, "admin"], qual_name=[]),
            code=lambda content, env: content + f"\nadmin.site.register({self.name})",
            deps={
                "admin": PyDependecy(
                    ident=PyIdent(module=["django", "contrib"], qual_name=["admin"]),
                ),
                f"{self.name}": PyDependecy(
                    ident=PyIdent(
                        module=[project_name, app_name, "models"], qual_name=[self.name]
                    ),
                ),
            },
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

        # add_apps_to_settings = PyCode(
        #     ident=PyIdent(
        #         module=[project_name, project_name, "settings"], qual_name=[]
        #     ),
        #     # todo Futher refinement for substitution logic
        #     code=lambda path: append_file(
        #         path,
        #         f"\nINSTALLED_APPS += ['{self.name_slug}']",
        #     ),
        #     strict_deps=[],
        #     weak_deps=[],
        # )

        add_apps_to_settings = PyCode(
            ident=PyIdent(
                module=[project_name, project_name, "settings"], qual_name=[]
            ),
            code=lambda content, env: content
            + f"\nINSTALLED_APPS += ['{self.name_slug}']",
            deps={},
        )

        # add_app_urls_to_project = PyCode(
        #     ident=PyIdent(module=[project_name, "urls"], qual_name=[]),
        #     code=lambda path: append_file(
        #         path,
        #         f"\nurlpatterns += [path('{self.name_slug}/', include('{self.name_slug}.urls'))]",
        #     ),
        #     strict_deps=[
        #         PyIdent(module=["django", "urls", "conf"], qual_name=["include"]),
        #     ],
        #     weak_deps=[],
        # )

        add_app_urls_to_project = PyCode(
            ident=PyIdent(module=[project_name, "urls"], qual_name=[]),
            code=lambda content, env: content
            + f"\nurlpatterns += [path('{self.name_slug}/', include('{self.name_slug}.urls'))]",
            deps={},
        )

        return [add_apps_to_settings, add_app_urls_to_project, *model_codes]


@dataclass
class DjangoProject:
    name: str
    apps: Iterable[DjangoApp]

    def to_py_codes(self) -> Iterable[PyCode]:
        app_codes = concat(map(lambda a: a.to_py_codes(self.name), self.apps))

        return app_codes

    def write(self, dir_path: Path) -> Io[None]:
        return foldl(
            lambda acc, code: acc.then(write_py_code(dir_path, code)),
            Io.pure(None),
            self.to_py_codes(),
        )


def validate(codes: Iterable[PyCode]) -> bool:
    def all_idents_unique(codes: Iterable[PyCode]) -> bool:
        idents = map(lambda c: c.ident, codes)

        def is_unique(acc: bool, id: PyIdent) -> bool:
            return acc and (id not in idents)

        return foldl(is_unique, True, idents)

    def all_deps_present(codes: Iterable[PyCode]) -> bool:
        for code in codes:
            # for dep in code.strict_deps + code.weak_deps:
            # for dep in concat([code.strict_deps, code.weak_deps]):
            for dep in code.deps.values():
                if dep not in [c.ident for c in codes]:
                    return False
        return True

    def no_strict_circular_deps(codes: Iterable[PyCode]) -> bool:
        def not_in_circle(visited: Iterable[PyIdent], code: PyCode) -> bool:
            if code.ident in visited:
                return False
            else:
                return all(
                    not_in_circle(concat([visited, [code.ident]]), c)
                    for c in codes
                    if c.ident in code.strict_deps()
                )

        return all(map(lambda c: not_in_circle([], c), codes))

    return (
        all_idents_unique(codes)
        and all_deps_present(codes)
        and no_strict_circular_deps(codes)
    )