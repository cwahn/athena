from ast import parse
from calendar import c
from enum import Enum
from http.client import HTTPConnection, HTTPResponse

from dataclasses import dataclass, field
from typing import Dict, Literal
from entoli.base.io import Io


def get_conn(host: str, post: int = 80) -> Io[HTTPConnection]:
    return Io(lambda: HTTPConnection(host, post))


type Method = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


def raw_request(
    conn: HTTPConnection,
    method: str,
    path: str,
    body: str = "",
    headers: dict[str, str] = {},
) -> Io[HTTPResponse]:
    conn.request(method, path, body, headers=headers)
    return Io(lambda: conn.getresponse())


def close_conn(conn: HTTPConnection) -> Io[None]:
    return Io(lambda: conn.close())


# ! Not frozen dataclass
@dataclass
class HttpSession:
    conn: HTTPConnection
    # cookies: Io[Dict[str, str]] = Io(lambda: {})
    cookies: Io[Dict[str, str]] = field(default_factory=lambda: Io(lambda: {}))


def get_session(host: str, port: int = 80) -> Io[HttpSession]:
    return get_conn(host, port).fmap(lambda conn: HttpSession(conn))


def session_from_conn(conn: HTTPConnection) -> Io[HttpSession]:
    return Io(lambda: HttpSession(conn))


def parse_cookies(header_str: str) -> Dict[str, str]:
    return dict(cookie.split("=") for cookie in header_str.split(";"))


def request(
    session: HttpSession,
    method: Method,
    path: str,
    body: str = "",
) -> Io[HTTPResponse]:
    def _request():
        conn = session.conn
        cookies = session.cookies.action()
        headers = {**cookies, "Content-Type": "application/json"}
        conn.request(method, path, body, headers=headers)
        res = conn.getresponse()
        new_cookies = parse_cookies(res.getheader("Set-Cookie", ""))
        session.cookies = Io(lambda: {**cookies, **new_cookies})
        return res

    return Io(_request)
