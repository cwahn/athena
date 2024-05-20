from datetime import timedelta
import sys
import os


# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from athena.django_dev.compile import PyCode, PyIdent, write_py_code

py_code = PyCode(
    ident=PyIdent(module=["auto_generated", "hello_world"], qual_name=["main"]),
    code=["print('Hello, world!')"],
    strict_deps=[PyIdent(module=["sys"], qual_name=["path"])],
    weak_deps=[],
)

write = write_py_code(py_code)

if __name__ == "__main__":
    write.action()
