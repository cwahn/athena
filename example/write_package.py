import sys
import os



# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)


from entoli.base.io import Io
from entoli.prelude import foldl
from entoli.system import append_file
from entoli.django_dev.py_code import PyCode, PyIdent, write_py_code


package_init_file = PyCode(
    ident=PyIdent(module=["auto_generated", "__init__"], qual_name=[]),
    # code=[],
    code=lambda path: Io.pure(None),
    strict_deps=[],
    weak_deps=[],
)

module_init_file = PyCode(
    ident=PyIdent(module=["auto_generated", "some_package", "__init__"], qual_name=[]),
    # code=[],
    code=lambda path: Io.pure(None),
    strict_deps=[],
    weak_deps=[],
)

def_greet = PyCode(
    ident=PyIdent(
        module=["auto_generated", "some_package", "some_module"], qual_name=["greet"]
    ),
    # code=[
    #     "greet = (",
    #     "    put_strln('What is your name?')",
    #     "    .then(get_str)",
    #     "    .and_then(lambda name: put_strln(f'Hello, {name}!'))",
    #     ")",
    # ],
    code=lambda path: append_file(
        path,
        "\n".join(
            [
                "greet = (",
                "    put_strln('What is your name?')",
                "    .then(get_str)",
                "    .and_then(lambda name: put_strln(f'Hello, {name}!'))",
                ")",
            ]
        ),
    ),
    strict_deps=[
        PyIdent(module=["src", "entoli", "base", "io"], qual_name=["put_strln"]),
        PyIdent(module=["src", "entoli", "base", "io"], qual_name=["get_str"]),
    ],
    weak_deps=[],
)

run_greet = PyCode(
    ident=PyIdent(module=["auto_generated", "run"], qual_name=["run_greet"]),
    # code=["if __name__ == '__main__':", "    greet.action()"],
    code=lambda path: append_file(
        path,
        "\n".join(
            [
                "if __name__ == '__main__':",
                "    greet.action()",
            ]
        ),
    ),
    strict_deps=[
        PyIdent(
            module=["some_package", "some_module"],
            qual_name=["greet"],
        )
    ],
    weak_deps=[],
)

write = foldl(
    lambda acc, code: acc.then(write_py_code(code)),
    Io.pure(None),
    [package_init_file, module_init_file, def_greet, run_greet],
)


if __name__ == "__main__":
    write.action()
