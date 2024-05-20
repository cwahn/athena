import sys
import os


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from athena.django_dev.compile import PyCode, PyIdent, write_py_code


package_init_file = PyCode(
    ident=PyIdent(module=["auto_generated", "__init__"], qual_name=[]),
    code=[],
    strict_deps=[],
    weak_deps=[],
)

module_init_file = PyCode(
    ident=PyIdent(module=["auto_generated", "some_package", "__init__"], qual_name=[]),
    code=[],
    strict_deps=[],
    weak_deps=[],
)

def_greet = PyCode(
    ident=PyIdent(
        module=["auto_generated", "some_package", "some_module"], qual_name=["greet"]
    ),
    code=[
        "greet = (",
        "    put_strln('What is your name?')",
        "    .then(get_str)",
        "    .and_then(lambda name: put_strln(f'Hello, {name}!'))",
        ")",
    ],
    strict_deps=[
        PyIdent(module=["src", "athena", "base", "io"], qual_name=["put_strln"]),
        PyIdent(module=["src", "athena", "base", "io"], qual_name=["get_str"]),
    ],
    weak_deps=[],
)

run_greet = PyCode(
    ident=PyIdent(module=["auto_generated_run"], qual_name=["run_greet"]),
    code=["if __name__ == '__main__':", "    greet.action()"],
    strict_deps=[
        PyIdent(
            module=["some_package", "some_module"],
            qual_name=["greet"],
        )
    ],
    weak_deps=[],
)

# write = write_py_code(def_greet).then(write_py_code(run_greet))
write = (
    write_py_code(package_init_file)
    .then(write_py_code(module_init_file))
    .then(write_py_code(def_greet))
    .then(write_py_code(run_greet))
)


if __name__ == "__main__":
    write.action()
