from datetime import timedelta
import sys
import os

# Add the src directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from entoli.base.io import Io, put_strln, get_str
from entoli.base.control import delay_for, loop


ask_and_sleep = (
    put_strln("How long should I sleep for? (in seconds)")
    ._(get_str)
    .__(
        lambda s: put_strln("Sleeping...")
        ._(delay_for(timedelta(seconds=int(s))))
        .__(lambda _: put_strln("Done!"))
    )
)

ask_and_sleep_loop = loop(ask_and_sleep)


if __name__ == "__main__":
    ask_and_sleep_loop.action()
