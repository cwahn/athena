from __future__ import annotations
from calendar import c
from dataclasses import dataclass
from math import e
from typing import Any, Callable, Generic, Iterable, Protocol, Tuple, Type, TypeVar

from networkx import line_graph

from entoli.base.typeclass import _A, _B, _A_co, Monad
from entoli.prelude import append, fst, snd, map


_S = TypeVar("_S")
_U = TypeVar("_U")
# _M = TypeVar("_M", bound=Monad)
_A = TypeVar("_A")
_B = TypeVar("_B")


@dataclass
class Parsec(Generic[_S, _U, _A]):
    un_parser: Callable[
        [
            State[_S, _U],  #
            Callable[[_A, State[_S, _U], ParseError], Any],  # consumed ok
            Callable[[ParseError], Any],  # consumed error
            Callable[[_A, State[_S, _U], ParseError], Any],  # empty ok
            Callable[[ParseError], Any],  # empty error
        ],
        Any,
    ]


@dataclass
class State(Generic[_S, _U]):
    state_input: _S
    state_pos: SourcePos
    state_user: _U


@dataclass
class SourcePos:
    name: str
    line: int
    col: int


@dataclass
class ParseError:
    source_pos: SourcePos
    message: str


# runParsecT :: Monad m => ParsecT s u m a -> State s u -> m (Consumed (m (Reply s u a)))
# {-# INLINABLE runParsecT #-}
# runParsecT p s = unParser p s cok cerr eok eerr
#     where cok a s' err = return . Consumed . return $ Ok a s' err
#           cerr err = return . Consumed . return $ Error err
#           eok a s' err = return . Empty . return $ Ok a s' err
#           eerr err = return . Empty . return $ Error err


type MbConsumed[_A] = Consumed[_A] | Empty


@dataclass
class Consumed(Generic[_A]):
    value: _A


@dataclass
class Empty(Generic[_A]):
    value: _A


type Reply[_S, _U, _A] = Reply_Ok[_S, _U, _A] | Reply_Error[_S, _U]


@dataclass
class Reply_Ok(Generic[_S, _U, _A]):
    s: _S
    state: State[_S, _U]
    err: ParseError


@dataclass
class Reply_Error(Generic[_S, _U]):
    err: ParseError


def run_parser(
    parser: Parsec[_S, _U, _A],
    state: State[_S, _U],
) -> Consumed[Reply[_S, _U, _A]]:
    def consumed_ok(a, s, err):  # -> Consumed[Reply_Ok[Any, Any, Any]]:
        return Consumed(Reply_Ok(s, a, err))

    def consumed_error(err):
        return Consumed(Reply_Error(err))

    def empty_ok(a, s, err):
        return Empty(Reply_Ok(s, a, err))

    def empty_error(err):
        return Empty(Reply_Error(err))

    return parser.un_parser(state, consumed_ok, consumed_error, empty_ok, empty_error)


# mkPT :: Monad m => (State s u -> m (Consumed (m (Reply s u a)))) -> ParsecT s u m a
# {-# INLINABLE mkPT #-}
# mkPT k = ParsecT $ \s cok cerr eok eerr -> do
#            cons <- k s
#            case cons of
#              Consumed mrep -> do
#                        rep <- mrep
#                        case rep of
#                          Ok x s' err -> cok x s' err
#                          Error err -> cerr err
#              Empty mrep -> do
#                        rep <- mrep
#                        case rep of
#                          Ok x s' err -> eok x s' err
#                          Error err -> eerr err


def mk_parser_t(
    k: Callable[[State[_S, _U]], Consumed[Reply[_S, _U, _A]]],
) -> Parsec[_S, _U, _A]:
    def un_parser(
        s: State[_S, _U],
        cok: Callable[[_A, State[_S, _U], ParseError], Any],
        cerr: Callable[[ParseError], Any],
        eok: Callable[[_A, State[_S, _U], ParseError], Any],
        eerr: Callable[[ParseError], Any],
    ) -> Any:
        cons = k(s)
        match cons:
            case Consumed(mrep):
                rep = mrep
                match rep:
                    case Reply_Ok(x, s_, err):
                        cok(x, s_, err)
                    case Reply_Error(err):
                        cerr(err)
            case Empty(mrep):
                rep = mrep
                match rep:
                    case Reply_Ok(x, s_, err):
                        eok(x, s_, err)
                    case Reply_Error(err):
                        eerr(err)

    return Parsec(un_parser)
