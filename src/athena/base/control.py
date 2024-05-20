from datetime import timedelta, datetime
from time import sleep

from entoli.base.io import Io


def loop(io: Io[None]) -> Io[None]:
    def _inner() -> None:
        while True:
            io.action()

    return Io(_inner)


def delay_for(delay: timedelta) -> Io[None]:
    return Io(lambda: sleep(delay.total_seconds()))


def delay_until(time_point: datetime) -> Io[None]:
    return Io(lambda: sleep((time_point - datetime.now()).total_seconds()))
