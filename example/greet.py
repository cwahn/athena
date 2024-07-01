import os
import sys

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.prelude import get_str, put_strln

greet = (
    put_strln("What is your name?")
    .then(get_str)
    .and_then(lambda name: put_strln(f"Hello, {name}!"))
)


if __name__ == "__main__":
    greet.action()
