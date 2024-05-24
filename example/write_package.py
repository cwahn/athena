from pathlib import Path
import sys
import os


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


from entoli.base.maybe import Just, Nothing
from entoli.map import Map
from entoli.base.io import Io, put_strln
from entoli.prelude import body, foldl
from entoli.system import append_file

# from entoli.django_dev.py_code import PyCode, PyIdent, write_py_code
from entoli.py_code.py_code import (
    PyCode,
    PyIdent,
    PyDependecy,
    write_code,
    write_codes,
    _all_deps_present,
    _all_idents_unique,
    _no_strict_circular_deps,
)


package_init_file = PyCode(
    ident=PyIdent(module=["some_package", "__init__"], mb_name=Nothing()),
    code=lambda refer, content: content,
    deps=Map(),
)

module_init_file = PyCode(
    ident=PyIdent(
        module=["some_package", "some_module", "__init__"],
        mb_name=Nothing(),
    ),
    code=lambda refer, content: content,
    deps=Map(),
)

def_greet = PyCode(
    ident=PyIdent(
        module=["some_package", "some_module", "some_submodule"],
        mb_name=Just("greet"),
    ),
    code=lambda refer, content: content
    + "\n".join(
        [
            "greet = (",
            f"    {refer('put_strln')}('What is your name?')",
            f"    .then({refer('get_str')})",
            f"    .and_then(lambda name: {refer('put_strln')}(f'Hello, {{name}}!'))",
            ")",
        ]
    ),
    deps=Map(
        [
            (
                "put_strln",
                PyDependecy(
                    ident=PyIdent(
                        module=["src", "entoli", "base", "io"],
                        mb_name=Just("put_strln"),
                    )
                ),
            ),
            (
                "get_str",
                PyDependecy(
                    ident=PyIdent(
                        module=["src", "entoli", "base", "io"],
                        mb_name=Just("get_str"),
                    )
                ),
            ),
        ]
    ),
)

run_greet = PyCode(
    ident=PyIdent(
        module=["some_package", "run"],
        mb_name=Just("run_greet"),
    ),
    code=lambda refer, content: content
    + "\n".join(
        [
            "if __name__ == '__main__':",
            f"    {refer('greet')}.action()",
        ]
    ),
    deps=Map(
        [
            (
                "greet",
                PyDependecy(
                    ident=PyIdent(
                        module=["some_package", "some_module", "some_submodule"],
                        mb_name=Just("greet"),
                    )
                ),
            ),
        ]
    ),
)

put_strln_ = PyCode(
    ident=PyIdent(module=["src", "entoli", "base", "io"], mb_name=Just("put_strln")),
    code=lambda refer, content: content,
    deps=Map(),
)

get_str_ = PyCode(
    ident=PyIdent(module=["src", "entoli", "base", "io"], mb_name=Just("get_str")),
    code=lambda refer, content: content,
    deps=Map(),
)


codes = [
    package_init_file,
    module_init_file,
    def_greet,
    run_greet,
    put_strln_,
    get_str_,
]

assert _all_idents_unique(codes)
assert _all_deps_present(codes)
assert _no_strict_circular_deps(codes)

main = write_codes(
    Path(__file__).parent.parent / "build",
    codes,
)


if __name__ == "__main__":
    main.action()
