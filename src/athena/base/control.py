from datetime import timedelta, datetime
from time import sleep

from athena.base.io import Io


def delay_for(delay: timedelta) -> Io[None]:
    return Io(lambda: sleep(delay.total_seconds()))


def delay_until(time_point: datetime) -> Io[None]:
    return Io(lambda: sleep((time_point - datetime.now()).total_seconds()))
