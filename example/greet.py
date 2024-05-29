import sys
import os

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.prelude import put_strln, get_str

greet = (
    put_strln("What is your name?")
    .then(get_str)
    .and_then(lambda name: put_strln(f"Hello, {name}!"))
)


if __name__ == "__main__":
    greet.action()
