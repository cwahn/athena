import os
import sys
from datetime import timedelta

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.control.concurrent import delay_for, loop
from entoli.prelude import get_str, put_strln

ask_and_sleep = (
    put_strln("How long should I sleep for? (in seconds)")
    .then(get_str)
    .and_then(
        lambda s: put_strln("Sleeping...")
        .then(delay_for(timedelta(seconds=int(s))))
        .and_then(lambda _: put_strln("Done!"))
    )
)

ask_and_sleep_loop = loop(ask_and_sleep)


if __name__ == "__main__":
    ask_and_sleep_loop.action()
