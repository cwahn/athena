from ast import parse
from enum import Enum
from http.client import HTTPConnection, HTTPResponse

from dataclasses import dataclass
from typing import Dict, Literal
from entoli.base.io import Io


def get_conn(host: str, post: int = 80) -> Io[HTTPConnection]:
    return Io(lambda: HTTPConnection(host, post))


type Method = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


def request(
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


# @dataclass
# class HttpSession:
#     conn: HTTPConnection
#     cookies: Io[Dict[str, str]] = Io(lambda: {})


# def get_session(host: str, port: int = 80) -> Io[HttpSession]:
#     return get_conn(host, port).map(lambda conn: HttpSession(conn))


# def session_from_conn(conn: HTTPConnection) -> Io[HttpSession]:
#     return Io(lambda: HttpSession(conn))


# def send_request(
#     session: HttpSession,
#     method: Method,
#     path: str,
#     body: str = "",
# ) -> Io[HTTPResponse]: ...


def parse_cookies(header_str: str) -> Dict[str, str]:
    return dict(cookie.split("=") for cookie in header_str.split(";"))
