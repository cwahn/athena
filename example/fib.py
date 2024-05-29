import functools
import sys
import os

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.prelude import put_strln, get_str


@functools.cache
def fib(n: int) -> int:
    match n:
        case 0:
            return 0
        case 1:
            return 1
        case _:
            return fib(n - 1) + fib(n - 2)


io_fib = (
    put_strln("Enter a number:")
    .then(get_str)
    .and_then(lambda s: put_strln(f"The {s}th Fibonacci number is {fib(int(s))}"))
)

if __name__ == "__main__":
    io_fib.action()
