from pathlib import Path
import sys
import os


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


from entoli.base.maybe import Just, Nothing
from entoli.map import Map
from entoli.base.io import Io
from entoli.prelude import body, foldl
from entoli.system import append_file

# from entoli.django_dev.py_code import PyCode, PyIdent, write_py_code
from entoli.py_code.py_code import PyCode, PyIdent, PyDependecy, write_code


package_init_file = PyCode(
    ident=PyIdent(module=["some_package", "__init__"], mb_name=Nothing()),
    code=lambda refer, content: content,
    # strict_deps=[],
    # weak_deps=[],
    deps=Map(),
)

# module_init_file = PyCode(
#     # ident=PyIdent(module=["auto_generated", "some_package", "__init__"], mb_name=[]),
#     ident=PyIdent(
#         module=["auto_generated", "some_package", "__init__"], mb_name=Nothing()
#     ),
#     # code=[],
#     code=lambda path: Io.pure(None),
#     strict_deps=[],
#     weak_deps=[],
# )
module_init_file = PyCode(
    ident=PyIdent(
        module=["some_package", "some_module", "__init__"],
        mb_name=Nothing(),
    ),
    code=lambda refer, content: content,
    deps=Map(),
)

# def_greet = PyCode(
#     # ident=PyIdent(
#     #     module=["auto_generated", "some_package", "some_module"], mb_name=["greet"]
#     # ),
#     ident=PyIdent(
#         module=["some_package", "some_module"],
#         mb_name=Just("greet"),
#     ),
#     code=lambda path: append_file(
#         path,
#         "\n".join(
#             [
#                 "greet = (",
#                 "    put_strln('What is your name?')",
#                 "    .then(get_str)",
#                 "    .and_then(lambda name: put_strln(f'Hello, {name}!'))",
#                 ")",
#             ]
#         ),
#     ),
#     strict_deps=[
#         # PyIdent(module=["src", "entoli", "base", "io"], mb_name=["put_strln"]),
#         PyIdent(module=["src", "entoli", "base", "io"], mb_name=Just("put_strln")),
#         # PyIdent(module=["src", "entoli", "base", "io"], mb_name=["get_str"]),
#         PyIdent(module=["src", "entoli", "base", "io"], mb_name=Just("get_str")),
#     ],
#     weak_deps=[],
# )
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

# run_greet = PyCode(
#     # ident=PyIdent(module=["auto_generated", "run"], mb_name=["run_greet"]),
#     ident=PyIdent(
#         module=["auto_generated", "run"],
#         mb_name=Just("run_greet"),
#     ),
#     # code=["if __name__ == '__main__':", "    greet.action()"],
#     code=lambda path: append_file(
#         path,
#         "\n".join(
#             [
#                 "if __name__ == '__main__':",
#                 "    greet.action()",
#             ]
#         ),
#     ),
#     strict_deps=[
#         PyIdent(
#             module=["some_package", "some_module"],
#             # mb_name=["greet"],
#             mb_name=Just("greet"),
#         )
#     ],
#     weak_deps=[],
# )

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
                        module=["some_package", "some_module"],
                        mb_name=Just("greet"),
                    )
                ),
            ),
        ]
    ),
)

write = foldl(
    lambda acc, code: acc.then(
        write_code(Path(__file__).parent.parent / "build", code)
    ),
    Io.pure(None),
    [package_init_file, module_init_file, def_greet, run_greet],
)


if __name__ == "__main__":
    write.action()
