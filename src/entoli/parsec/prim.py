from __future__ import annotations
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    TypeVar,
    Union,
)


from entoli.data.alternative import Alternative
from entoli.prelude import Io
from entoli.data.monad_plus import MonadPlus
from entoli.data.maybe import Just, Maybe, Nothing


from entoli.data.monad import Monad

from entoli.prelude import (
    append,
    foldl,
    put_strln,
    id,
    uncons,
    filter,
)


_S = TypeVar("_S")
_U = TypeVar("_U")
_M = TypeVar("_M", bound=Monad)
_A = TypeVar("_A")
_B = TypeVar("_B")

_T = TypeVar("_T")

# type _M[_B] = Monad[_B]

# newtype ParsecT s u m a
#     = ParsecT {unParser :: forall b .
#                  State s u
#               -> (a -> State s u -> ParseError -> m b) -- consumed ok
#               -> (ParseError -> m b)                   -- consumed err
#               -> (a -> State s u -> ParseError -> m b) -- empty ok
#               -> (ParseError -> m b)                   -- empty err
#               -> m b
#              }
#      deriving ( Typeable )


@dataclass(frozen=True, slots=True)
class Parsec(Generic[_S, _U, _A], MonadPlus[_A], Alternative[_A]):
    un_parser: Callable[
        [
            State[_S, _U],
            Callable[[_A, State[_S, _U], ParseError], Any],
            Callable[[ParseError], Any],
            Callable[[_A, State[_S, _U], ParseError], Any],
            Callable[[ParseError], Any],
        ],
        Any,
    ]

    # parsecMap :: (a -> b) -> ParsecT s u m a -> ParsecT s u m b
    # parsecMap f p
    #     = ParsecT $ \s cok cerr eok eerr ->
    #       unParser p s (cok . f) cerr (eok . f) eerr

    def fmap(self, f: Callable[[_A], _B]) -> "Parsec[_S, _U, _B]":
        return Parsec(
            lambda s, cok, cerr, eok, eerr: self.un_parser(
                s,
                lambda a, s_, err: cok(f(a), s_, err),
                cerr,
                lambda a, s_, err: eok(f(a), s_, err),
                eerr,
            )
        )

    # parserReturn :: a -> ParsecT s u m a
    # parserReturn x
    #     = ParsecT $ \s _ _ eok _ ->
    #       eok x s (unknownError s)

    @staticmethod
    def pure(x: _A) -> "Parsec[_S, _U, _A]":
        return Parsec(lambda s, _0, _1, eok, _2: eok(x, s, unknown_error(s)))

    def ap(self, f: "Parsec[_S, _U, Callable[[_A], _B]]") -> "Parsec[_S, _U, _B]":
        return f.and_then(lambda f_: self.and_then(lambda x_: Parsec.pure(f_(x_))))

    # parserBind :: ParsecT s u m a -> (a -> ParsecT s u m b) -> ParsecT s u m b
    # {-# INLINE parserBind #-}
    # parserBind m k
    #   = ParsecT $ \s cok cerr eok eerr ->
    #     let
    #         -- consumed-okay case for m
    #         mcok x s err
    #           | errorIsUnknown err = unParser (k x) s cok cerr cok cerr
    #           | otherwise =
    #             let
    #                  -- if (k x) consumes, those go straight up
    #                  pcok = cok
    #                  pcerr = cerr

    #                  -- if (k x) doesn't consume input, but is okay,
    #                  -- we still return in the consumed continuation
    #                  peok x s err' = cok x s (mergeError err err')

    #                  -- if (k x) doesn't consume input, but errors,
    #                  -- we return the error in the 'consumed-error'
    #                  -- continuation
    #                  peerr err' = cerr (mergeError err err')
    #             in  unParser (k x) s pcok pcerr peok peerr

    #         -- empty-ok case for m
    #         meok x s err
    #           | errorIsUnknown err = unParser (k x) s cok cerr eok eerr
    #           | otherwise =
    #             let
    #                 -- in these cases, (k x) can return as empty
    #                 pcok = cok
    #                 peok x s err' = eok x s (mergeError err err')
    #                 pcerr = cerr
    #                 peerr err' = eerr (mergeError err err')
    #             in  unParser (k x) s pcok pcerr peok peerr
    #         -- consumed-error case for m
    #         mcerr = cerr

    #         -- empty-error case for m
    #         meerr = eerr

    #     in unParser m s mcok mcerr meok meerr

    def and_then(self, f: Callable[[_A], "Parsec[_S, _U, _B]"]) -> "Parsec[_S, _U, _B]":
        def _un_parser(
            s: State[_S, _U],
            cok: Callable[[_B, State[_S, _U], ParseError], Any],
            cerr: Callable[[ParseError], Any],
            eok: Callable[[_B, State[_S, _U], ParseError], Any],
            eerr: Callable[[ParseError], Any],
        ) -> Any:
            def mcok(x, s, err):
                if err == unknown_error(s):
                    return f(x).un_parser(s, cok, cerr, cok, cerr)
                else:
                    pcok = cok
                    pcerr = cerr

                    def peok(x, s, err_):
                        return cok(x, s, merge_error(err, err_))

                    def peerr(err_):
                        return cerr(merge_error(err, err_))

                    return f(x).un_parser(s, pcok, pcerr, peok, peerr)

            def meok(x, s, err):
                if err == unknown_error(s):
                    return f(x).un_parser(s, cok, cerr, eok, eerr)
                else:
                    pcok = cok

                    def peok(x, s, err_):
                        return eok(x, s, merge_error(err, err_))

                    pcerr = cerr

                    def peerr(err_):
                        return eerr(merge_error(err, err_))

                    return f(x).un_parser(s, pcok, pcerr, peok, peerr)

            return self.un_parser(s, mcok, cerr, meok, eerr)

        return Parsec(_un_parser)

    @staticmethod
    def mzero() -> "Parsec[_S, _U, _A]":
        return Parsec(lambda s, _0, _1, _2, eerr: eerr(unknown_error(s)))

    # parserPlus :: ParsecT s u m a -> ParsecT s u m a -> ParsecT s u m a
    # {-# INLINE parserPlus #-}
    # parserPlus m n
    #     = ParsecT $ \s cok cerr eok eerr ->
    #       let
    #           meerr err =
    #               let
    #                   neok y s' err' = eok y s' (mergeError err err')
    #                   neerr err' = eerr $ mergeError err err'
    #               in unParser n s cok cerr neok neerr
    #       in unParser m s cok cerr eok meerr

    def mplus(self, other: "Parsec[_S, _U, _A]") -> "Parsec[_S, _U, _A]":
        def _un_parser(
            s: State[_S, _U],
            cok: Callable[[_A, State[_S, _U], ParseError], Any],
            cerr: Callable[[ParseError], Any],
            eok: Callable[[_A, State[_S, _U], ParseError], Any],
            eerr: Callable[[ParseError], Any],
        ) -> Any:
            def meerr(err):
                def neok(y, s_, err_):
                    return eok(y, s_, merge_error(err, err_))

                def neerr(err_):
                    return eerr(merge_error(err, err_))

                return other.un_parser(s, cok, cerr, neok, neerr)

            return self.un_parser(s, cok, cerr, eok, meerr)

        return Parsec(_un_parser)

    @staticmethod
    def empty() -> "Parsec[_S, _U, _A]":
        return Parsec(lambda s, _0, _1, _2, eerr: eerr(unknown_error(s)))

    def or_else(self, other: "Parsec[_S, _U, _A]") -> "Parsec[_S, _U, _A]":
        return self.mplus(other)

    def then(self, x: "Parsec[_S, _U, _B]") -> "Parsec[_S, _U, _B]":
        return self.and_then(lambda _: x)

    # some :: f a -> f [a]
    # some v = some_v
    #   where
    #     many_v = some_v <|> pure []
    #     some_v = (:) <$> v <*> many_v

    # many :: f a -> f [a]
    # many v = many_v
    #   where
    #     many_v = some_v <|> pure []
    #     some_v = (:) <$> v <*> many_v

    def some(self) -> "Parsec[_S, _U, Iterable[_A]]":
        return self.and_then(
            lambda x: self.some()
            .fmap(lambda xs: append([x], xs))
            .mplus(Parsec.pure([x]))
        )

    def many(self) -> "Parsec[_S, _U, Iterable[_A]]":
        return self.some().mplus(Parsec.pure([]))


# -- | The parser @unexpected msg@ always fails with an unexpected error
# -- message @msg@ without consuming any input.
# --
# -- The parsers 'fail', ('<?>') and @unexpected@ are the three parsers
# -- used to generate error messages. Of these, only ('<?>') is commonly
# -- used. For an example of the use of @unexpected@, see the definition
# -- of 'Text.Parsec.Combinator.notFollowedBy'.

# unexpected :: (Stream s m t) => String -> ParsecT s u m a
# unexpected msg
#     = ParsecT $ \s _ _ _ eerr ->
#       eerr $ newErrorMessage (UnExpect msg) (statePos s)


def unexpected(msg: str) -> Parsec[_S, _U, _A]:
    return Parsec(
        lambda s, _0, _1, _2, eerr: eerr(new_error_message(UnExpect(msg), s.pos))
    )


# runParsecT :: Monad m => ParsecT s u m a -> State s u -> m (Consumed (m (Reply s u a)))
# {-# INLINABLE runParsecT #-}
# runParsecT p s = unParser p s cok cerr eok eerr
#     where cok a s' err = return . Consumed . return $ Ok a s' err
#           cerr err = return . Consumed . return $ Error err
#           eok a s' err = return . Empty . return $ Ok a s' err
#           eerr err = return . Empty . return $ Error err


def run_parsec_t(
    parser: Parsec[_S, _U, _A],
    state: State[_S, _U],
) -> MbConsumed[Reply[_S, _U, _A]]:
    def cok(a, s_, err):
        return Consumed(Reply_Ok(a, s_, err))

    def cerr(err):
        return Consumed(Reply_Error(err))

    def eok(a, s_, err):
        return Empty(Reply_Ok(a, s_, err))

    def eerr(err):
        return Empty(Reply_Error(err))

    return parser.un_parser(state, cok, cerr, eok, eerr)


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


def make_parser(
    k: Callable[[State[_S, _U]], MbConsumed[Reply[_S, _U, _A]]],
) -> Parsec[_S, _U, _A]:
    def _un_parser(
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

    return Parsec(_un_parser)


@dataclass(frozen=True, slots=True)
class State(Generic[_S, _U]):
    input: _S
    pos: SourcePos
    user_state: _U


@dataclass(frozen=True, slots=True)
class SourcePos:
    name: str
    line: int
    col: int

    def __lt__(self, other: SourcePos) -> bool:
        if self.line < other.line:
            return True
        if self.line == other.line:
            return self.col < other.col
        return False


# newPos :: SourceName -> Line -> Column -> SourcePos
# newPos name line column
#     = SourcePos name line column


def new_pos(
    name: str,
    line: int,
    column: int,
) -> SourcePos:
    return SourcePos(name, line, column)


# initialPos :: SourceName -> SourcePos
# initialPos name
#     = newPos name 1 1


def initial_pos(
    name: str,
) -> SourcePos:
    return new_pos(name, 1, 1)


# updatePosString :: SourcePos -> String -> SourcePos
# updatePosString pos string
#     = foldl updatePosChar pos string


def update_pos_string(
    pos: SourcePos,
    string: Iterable[str],
) -> SourcePos:
    return foldl(update_pos_char, pos, string)


# updatePosChar   :: SourcePos -> Char -> SourcePos
# updatePosChar (SourcePos name line column) c
#     = case c of
#         '\n' -> SourcePos name (line+1) 1
#         '\t' -> SourcePos name line (column + 8 - ((column-1) `mod` 8))
#         _    -> SourcePos name line (column + 1)


def update_pos_char(
    pos: SourcePos,
    c: str,
) -> SourcePos:
    match c:
        case "\n":
            return new_pos(pos.name, pos.line + 1, 1)
        case "\t":
            return new_pos(pos.name, pos.line, pos.col + 8 - ((pos.col - 1) % 8))
        case _:
            return new_pos(pos.name, pos.line, pos.col + 1)


type Message = SysUnExpect | UnExpect | Expect | RawMessage

# SysUnExpect = NewType("SysUnExpect", str)
# UnExpect = NewType("UnExpect", str)
# Expect = NewType("Expect", str)
# RawMessage = NewType("RawMessage", str)


@dataclass(frozen=True, slots=True)
class SysUnExpect:
    value: str


@dataclass(frozen=True, slots=True)
class UnExpect:
    value: str


@dataclass(frozen=True, slots=True)
class Expect:
    value: str


@dataclass(frozen=True, slots=True)
class RawMessage:
    value: str


class _TestMessage:
    def _test_equality(self):
        assert not (SysUnExpect("a") == UnExpect("a"))

        assert SysUnExpect("a") == SysUnExpect("a")
        assert UnExpect("a") == UnExpect("a")
        assert Expect("a") == Expect("a")
        assert RawMessage("a") == RawMessage("a")


@dataclass(frozen=True, slots=True)
class ParseError:
    source_pos: SourcePos
    message: Iterable[Message]


# newErrorUnknown :: SourcePos -> ParseError
# newErrorUnknown pos
#     = ParseError pos []


def new_error_unknown(
    pos: SourcePos,
) -> ParseError:
    return ParseError(pos, [])


# newErrorMessage :: Message -> SourcePos -> ParseError
# newErrorMessage msg pos
#     = ParseError pos [msg]


def new_error_message(
    msg: Message,
    pos: SourcePos,
) -> ParseError:
    return ParseError(pos, [msg])


# setErrorMessage :: Message -> ParseError -> ParseError
# setErrorMessage msg (ParseError pos msgs)
#     = ParseError pos (msg : filter (msg /=) msgs)


def set_error_message(
    msg: Message,
    e: ParseError,
) -> ParseError:
    return ParseError(
        e.source_pos, append([msg], filter(lambda m: m != msg, e.message))
    )


# mergeError :: ParseError -> ParseError -> ParseError
# mergeError e1@(ParseError pos1 msgs1) e2@(ParseError pos2 msgs2)
#     -- prefer meaningful errors
#     | null msgs2 && not (null msgs1) = e1
#     | null msgs1 && not (null msgs2) = e2
#     | otherwise
#       -- perfectly we'd compare the consumed token count
#       -- https://github.com/haskell/parsec/issues/175
#     = case compareErrorPos pos1 pos2 of
#         -- select the longest match
#         EQ -> ParseError pos1 (msgs1 ++ msgs2)
#         GT -> e1
#         LT -> e2


def merge_error(
    e1: ParseError,
    e2: ParseError,
) -> ParseError:
    if not e2.message and e1.message:
        return e1
    if not e1.message and e2.message:
        return e2
    if e1.source_pos == e2.source_pos:
        return ParseError(e1.source_pos, append(e1.message, e2.message))
    if e1.source_pos < e2.source_pos:
        return e1
    else:
        return e2


type MbConsumed[_A] = Consumed[_A] | Empty


@dataclass(frozen=True, slots=True)
class Consumed(Generic[_A]):
    value: _A


@dataclass(frozen=True, slots=True)
class Empty(Generic[_A]):
    value: _A


type Reply[_S, _U, _A] = Reply_Error | Reply_Ok[_S, _U, _A]


@dataclass(frozen=True, slots=True)
class Reply_Error:
    err: ParseError


@dataclass(frozen=True, slots=True)
class Reply_Ok(Generic[_S, _U, _A]):
    a: _A
    state: State[_S, _U]
    err: ParseError


# tokens :: (Stream s m t, Eq t)
#        => ([t] -> String)      -- Pretty print a list of tokens
#        -> (SourcePos -> [t] -> SourcePos)
#        -> [t]                  -- List of tokens to parse
#        -> ParsecT s u m [t]
# {-# INLINE tokens #-}
# tokens _ _ []
#     = ParsecT $ \s _ _ eok _ ->
#       eok [] s $ unknownError s
# tokens showTokens nextposs tts@(tok:toks)
#     = ParsecT $ \(State input pos u) cok cerr _eok eerr ->
#     let
#         errEof = (setErrorMessage (Expect (showTokens tts))
#                   (newErrorMessage (SysUnExpect "") pos))

#         errExpect x = (setErrorMessage (Expect (showTokens tts))
#                        (newErrorMessage (SysUnExpect (showTokens [x])) pos))

#         walk []     rs = ok rs
#         walk (t:ts) rs = do
#           sr <- uncons rs
#           case sr of
#             Nothing                 -> cerr $ errEof
#             Just (x,xs) | t == x    -> walk ts xs
#                         | otherwise -> cerr $ errExpect x

#         ok rs = let pos' = nextposs pos tts
#                     s' = State rs pos' u
#                 in cok tts s' (newErrorUnknown pos')
#     in do
#         sr <- uncons input
#         case sr of
#             Nothing         -> eerr $ errEof
#             Just (x,xs)
#                 | tok == x  -> walk toks xs
#                 | otherwise -> eerr $ errExpect x


def tokens(
    show_tokens: Callable[[Iterable[_T]], str],
    next_pos: Callable[[SourcePos, Iterable[_T]], SourcePos],
    tts: Iterable[_T],
) -> Parsec[Iterable[_T], _U, Iterable[_T]]:
    match uncons(tts):
        case Nothing():
            return Parsec(lambda s, _0, _1, eok, _2: eok([], s, unknown_error(s)))
        case Just((tok, toks)):
            # tok = head(ts)
            # toks = tail(ts)

            def _un_parser(
                s: State[Iterable[_T], _U],
                cok: Callable[[Iterable[_T], State[Iterable[_T], _U], ParseError], Any],
                cerr: Callable[[ParseError], Any],
                _eok: Callable[
                    [Iterable[_T], State[Iterable[_T], _U], ParseError], Any
                ],
                eerr: Callable[[ParseError], Any],
            ) -> Any:
                err_eof = set_error_message(
                    Expect(show_tokens(tts)),
                    new_error_message(SysUnExpect(""), s.pos),
                )

                def err_expect(x):
                    return set_error_message(
                        Expect(show_tokens(tts)),
                        new_error_message(SysUnExpect(show_tokens([x])), s.pos),
                    )

                def walk(ts: Iterable[_T], rs: Iterable[_T]) -> Any:
                    # match ts:
                    match uncons(ts):
                        case Nothing():
                            return ok(rs)
                        case Just((t, ts)):
                            sr = uncons(rs)
                            match sr:
                                case Nothing():
                                    return cerr(err_eof)
                                case Just((x, xs)):
                                    if t == x:
                                        return walk(ts, xs)
                                    else:
                                        return cerr(err_expect(x))

                def ok(rs: Iterable[_T]) -> Any:
                    pos_ = next_pos(s.pos, tts)
                    s_ = State(rs, pos_, s.user_state)
                    return cok(tts, s_, new_error_unknown(pos_))

                sr = uncons(s.input)

                match sr:
                    case Nothing():
                        return eerr(err_eof)
                    case Just((x, xs)):
                        if tok == x:
                            return walk(toks, xs)
                        else:
                            return eerr(err_expect(x))

            return Parsec(_un_parser)


# -- | Like 'tokens', but doesn't consume matching prefix.
# --
# -- @since 3.1.16.0
# tokens' :: (Stream s m t, Eq t)
#        => ([t] -> String)      -- Pretty print a list of tokens
#        -> (SourcePos -> [t] -> SourcePos)
#        -> [t]                  -- List of tokens to parse
#        -> ParsecT s u m [t]
# {-# INLINE tokens' #-}
# tokens' _ _ []
#     = ParsecT $ \s _ _ eok _ ->
#       eok [] s $ unknownError s
# tokens' showTokens nextposs tts@(tok:toks)
#     = ParsecT $ \(State input pos u) cok _cerr _eok eerr ->
#     let
#         errEof = (setErrorMessage (Expect (showTokens tts))
#                   (newErrorMessage (SysUnExpect "") pos))

#         errExpect x = (setErrorMessage (Expect (showTokens tts))
#                        (newErrorMessage (SysUnExpect (showTokens [x])) pos))

#         walk []     rs = ok rs
#         walk (t:ts) rs = do
#           sr <- uncons rs
#           case sr of
#             Nothing                 -> eerr $ errEof
#             Just (x,xs) | t == x    -> walk ts xs
#                         | otherwise -> eerr $ errExpect x

#         ok rs = let pos' = nextposs pos tts
#                     s' = State rs pos' u
#                 in cok tts s' (newErrorUnknown pos')
#     in do
#         sr <- uncons input
#         case sr of
#             Nothing         -> eerr $ errEof
#             Just (x,xs)
#                 | tok == x  -> walk toks xs
#                 | otherwise -> eerr $ errExpect x


def tokens_(
    show_tokens: Callable[[Iterable[_T]], str],
    next_pos: Callable[[SourcePos, Iterable[_T]], SourcePos],
    tts: Iterable[_T],
) -> Parsec[Iterable[_T], _U, Iterable[_T]]:
    # match tts:
    match uncons(tts):
        case Nothing():
            return Parsec(lambda s, _0, _1, eok, _2: eok([], s, unknown_error(s)))
        case Just((tok, toks)):

            def _un_parser(
                s: State[Iterable[_T], _U],
                cok: Callable[[Iterable[_T], State[Iterable[_T], _U], ParseError], Any],
                _cerr: Callable[[ParseError], Any],
                _eok: Callable[
                    [Iterable[_T], State[Iterable[_T], _U], ParseError], Any
                ],
                eerr: Callable[[ParseError], Any],
            ) -> Any:
                err_eof = set_error_message(
                    Expect(show_tokens(tts)),
                    new_error_message(SysUnExpect(""), s.pos),
                )

                def err_expect(x):
                    return set_error_message(
                        Expect(show_tokens(tts)),
                        new_error_message(SysUnExpect(show_tokens([x])), s.pos),
                    )

                def walk(ts: Iterable[_T], rs: Iterable[_T]) -> Any:
                    match uncons(ts):
                        case Nothing():
                            return ok(rs)
                        case Just((t, ts)):
                            sr = uncons(rs)
                            match sr:
                                case Nothing():
                                    return eerr(err_eof)
                                case Just((x, xs)):
                                    if t == x:
                                        return walk(ts, xs)
                                    else:
                                        return eerr(err_expect(x))

                def ok(rs: Iterable[_T]) -> Any:
                    pos_ = next_pos(s.pos, tts)
                    s_ = State(rs, pos_, s.user_state)
                    return cok(tts, s_, new_error_unknown(pos_))

                sr = uncons(s.input)

                match sr:
                    case Nothing():
                        return eerr(err_eof)
                    case Just((x, xs)):
                        if tok == x:
                            return walk(toks, xs)
                        else:
                            return eerr(err_expect(x))

            return Parsec(_un_parser)


# tokenPrim :: (Stream s m t)
#           => (t -> String)                      -- ^ Token pretty-printing function.
#           -> (SourcePos -> t -> s -> SourcePos) -- ^ Next position calculating function.
#           -> (t -> Maybe a)                     -- ^ Matching function for the token to parse.
#           -> ParsecT s u m a
# {-# INLINE tokenPrim #-}
# tokenPrim showToken nextpos test = tokenPrimEx showToken nextpos Nothing test


def token_prim(
    show_token: Callable[[_T], str],
    next_pos: Callable[[SourcePos, _T, Iterable[_T]], SourcePos],
    test: Callable[[_T], Maybe[_A]],
) -> Parsec[Iterable[_T], _U, _A]:
    return token_prim_ex(show_token, next_pos, Nothing(), test)


# tokenPrimEx :: (Stream s m t)
#             => (t -> String)
#             -> (SourcePos -> t -> s -> SourcePos)
#             -> Maybe (SourcePos -> t -> s -> u -> u)
#             -> (t -> Maybe a)
#             -> ParsecT s u m a
# {-# INLINE tokenPrimEx #-}
# tokenPrimEx showToken nextpos Nothing test
#   = ParsecT $ \(State input pos user) cok _cerr _eok eerr -> do
#       r <- uncons input
#       case r of
#         Nothing -> eerr $ unexpectError "" pos
#         Just (c,cs)
#          -> case test c of
#               Just x -> let newpos = nextpos pos c cs
#                             newstate = State cs newpos user
#                         in seq newpos $ seq newstate $
#                            cok x newstate (newErrorUnknown newpos)
#               Nothing -> eerr $ unexpectError (showToken c) pos
# tokenPrimEx showToken nextpos (Just nextState) test
#   = ParsecT $ \(State input pos user) cok _cerr _eok eerr -> do
#       r <- uncons input
#       case r of
#         Nothing -> eerr $ unexpectError "" pos
#         Just (c,cs)
#          -> case test c of
#               Just x -> let newpos = nextpos pos c cs
#                             newUser = nextState pos c cs user
#                             newstate = State cs newpos newUser
#                         in seq newpos $ seq newstate $
#                            cok x newstate $ newErrorUnknown newpos
#               Nothing -> eerr $ unexpectError (showToken c) pos


def token_prim_ex(
    show_token: Callable[[_T], str],
    next_pos: Callable[[SourcePos, _T, Iterable[_T]], SourcePos],
    next_state: Maybe[Callable[[SourcePos, _T, Iterable[_T], _U], _U]],
    test: Callable[[_T], Maybe[_A]],
) -> Parsec[Iterable[_T], _U, _A]:
    def _un_parser(
        s: State[Iterable[_T], _U],
        cok: Callable[[_A, State[Iterable[_T], _U], ParseError], Any],
        _cerr: Callable[[ParseError], Any],
        _eok: Callable[[_A, State[Iterable[_T], _U], ParseError], Any],
        eerr: Callable[[ParseError], Any],
    ) -> Any:
        r = uncons(s.input)
        match r:
            case Nothing():
                return eerr(new_error_message(SysUnExpect(""), s.pos))
            case Just((c, cs)):
                match test(c):
                    case Nothing():
                        return eerr(
                            new_error_message(SysUnExpect(show_token(c)), s.pos)
                        )
                    case Just(x):
                        new_pos = next_pos(s.pos, c, cs)
                        new_state = State(cs, new_pos, s.user_state)
                        return cok(x, new_state, new_error_unknown(new_pos))

    return Parsec(_un_parser)


# token :: (Stream s Identity t)
#       => (t -> String)            -- ^ Token pretty-printing function.
#       -> (t -> SourcePos)         -- ^ Computes the position of a token.
#       -> (t -> Maybe a)           -- ^ Matching function for the token to parse.
#       -> Parsec s u a
# {-# INLINABLE token #-}
# token showToken tokpos test = tokenPrim showToken nextpos test
#     where
#         nextpos _ tok ts = case runIdentity (uncons ts) of
#                              Nothing -> tokpos tok
#                              Just (tok',_) -> tokpos tok'


def token(
    show_token: Callable[[_T], str],
    tok_pos: Callable[[_T], SourcePos],
    test: Callable[[_T], Maybe[_A]],
) -> Parsec[Iterable[_T], _U, _A]:
    return token_prim(show_token, lambda _, tok, ts: tok_pos(tok), test)


# unknownError :: State s u -> ParseError
# unknownError state        = newErrorUnknown (statePos state)


def unknown_error(
    state: State[_S, _U],
) -> ParseError:
    return new_error_unknown(state.pos)


# many :: ParsecT s u m a -> ParsecT s u m [a]
# many p
#   = do xs <- manyAccum (:) p
#        return (reverse xs)


def many(
    p: Parsec[_S, _U, _A],
) -> Parsec[_S, _U, Iterable[_A]]:
    return p.many()


# many1 :: ParsecT s u m a -> ParsecT s u m [a]
# {-# INLINABLE many1 #-}
# many1 p = do{ x <- p; xs <- many p; return (x:xs) }


def many1(
    p: Parsec[_S, _U, _A],
) -> Parsec[_S, _U, Iterable[_A]]:
    # return Parsec.bind(
    #     p, lambda x: Parsec.bind(many(p), lambda xs: Parsec.pure([x] + xs))
    # )
    return p.and_then(lambda x: p.many().fmap(lambda xs: append([x], xs)))


# skipMany :: ParsecT s u m a -> ParsecT s u m ()
# skipMany p
#   = do _ <- manyAccum (\_ _ -> []) p
#        return ()


def skip_many(
    p: Parsec[_S, _U, _A],
) -> Parsec[_S, _U, None]:
    # return Parsec.bind(many_accum(lambda _0, _1: [], p), lambda _: Parsec.pure(None))
    return many_accum(lambda _0, _1: [], p).then(Parsec.pure(None))


# manyAccum :: (a -> [a] -> [a])
#           -> ParsecT s u m a
#           -> ParsecT s u m [a]
# manyAccum acc p =
#     ParsecT $ \s cok cerr eok _eerr ->
#     let walk xs x s' _err =
#             unParser p s'
#               (seq xs $ walk $ acc x xs)  -- consumed-ok
#               cerr                        -- consumed-err
#               manyErr                     -- empty-ok
#               (\e -> cok (acc x xs) s' e) -- empty-err
#     in unParser p s (walk []) cerr manyErr (\e -> eok [] s e)


def many_accum(
    acc: Callable[[_A, Iterable[_A]], Iterable[_A]],
    p: Parsec[_S, _U, _A],
) -> Parsec[_S, _U, Iterable[_A]]:
    def _un_parser(
        s: State[_S, _U],
        cok: Callable[[Iterable[_A], State[_S, _U], ParseError], Any],
        cerr: Callable[[ParseError], Any],
        eok: Callable[[Iterable[_A], State[_S, _U], ParseError], Any],
        _eerr: Callable[[ParseError], Any],
    ) -> Any:
        def walk(
            xs: Iterable[_A],
            x: _A,
            s_: State[_S, _U],
            _err: ParseError,
        ) -> Any:
            return p.un_parser(
                s_,
                lambda x_, s_, err: walk(acc(x, xs), x_, s_, err),
                cerr,
                lambda _0, _1, _2: many_err(),
                lambda e: cok(acc(x, xs), s_, e),
            )

        return p.un_parser(
            s,
            lambda x, s_, err: walk([], x, s_, err),
            cerr,
            lambda _0, _1, _2: many_err(),
            lambda e: eok([], s, e),
        )

    return Parsec(_un_parser)


def many_err() -> Any:
    raise Exception(
        "combinator 'many' is applied to a parser that accepts an empty string."
    )


# runPT :: (Stream s m t)
#       => ParsecT s u m a -> u -> SourceName -> s -> m (Union ParseError a)
# {-# INLINABLE runPT #-}
# runPT p u name s
#     = do res <- runParsecT p (State s (initialPos name) u)
#          r <- parserReply res
#          case r of
#            Ok x _ _  -> return (Right x)
#            Error err -> return (Left err)
#     where
#         parserReply res
#             = case res of
#                 Consumed r -> r
#                 Empty    r -> r


def run_pt(
    p: Parsec[Iterable[_T], _U, _A],
    u: _U,
    name: str,
    s: Iterable[_T],
) -> Union[ParseError, _A]:
    res = run_parsec_t(p, State(s, initial_pos(name), u))

    def parser_reply(
        res: MbConsumed[Reply[Iterable[_T], _U, _A]],
    ) -> Reply[Iterable[_T], _U, _A]:
        match res:
            case Consumed(r):
                return r
            case Empty(r):
                return r

    r = parser_reply(res)

    match r:
        case Reply_Ok(x, _, _):
            return x
        case Reply_Error(err):
            return err


# runP :: (Stream s Identity t)
#      => Parsec s u a -> u -> SourceName -> s -> Union ParseError a
# runP p u name s = runIdentity $ runPT p u name s


def run_p(
    p: Parsec[Iterable[_T], _U, _A],
    u: _U,
    name: str,
    s: Iterable[_T],
) -> Union[ParseError, _A]:
    return run_pt(p, u, name, s)


# runParserT :: (Stream s m t)
#            => ParsecT s u m a -> u -> SourceName -> s -> m (Union ParseError a)
# runParserT = runPT


# ! Maybe redundant


def run_parser_t(
    p: Parsec[Iterable[_T], _U, _A],
    u: _U,
    name: str,
    s: Iterable[_T],
) -> Union[ParseError, _A]:
    return run_pt(p, u, name, s)


# runParser :: (Stream s Identity t)
#           => Parsec s u a -> u -> SourceName -> s -> Union ParseError a
# runParser = runP

# ! Maybe redundant


def run_parser(
    p: Parsec[Iterable[_T], _U, _A],
    u: _U,
    name: str,
    s: Iterable[_T],
) -> Union[ParseError, _A]:
    return run_p(p, u, name, s)


# parse :: (Stream s Identity t)
#       => Parsec s () a -> SourceName -> s -> Union ParseError a
# parse p = runP p ()

# ! Maybe redundant


def parse(
    p: Parsec[Iterable[_T], None, _A],
    name: str,
    s: Iterable[_T],
) -> Union[ParseError, _A]:
    return run_p(p, None, name, s)


# parseTest :: (Stream s Identity t, Show a)
#           => Parsec s () a -> s -> IO ()
# parseTest p input
#     = case parse p "" input of
#         Left err -> do putStr "parse error at "
#                        print err
#         Right x  -> print x


def parse_test(
    p: Parsec[Iterable[_T], None, _A],
    input: Iterable[_T],
) -> Io[None]:
    match parse(p, "", input):
        case ParseError(pos, msg):
            return put_strln("parse error at " + str(pos))
        case x:
            return put_strln(str(x))


# -- < Parser state combinators

# -- | Returns the current source position. See also 'SourcePos'.

# getPosition :: (Monad m) => ParsecT s u m SourcePos
# getPosition = do state <- getParserState
#                  return (statePos state)


def get_position() -> Parsec[Iterable[_T], _U, SourcePos]:
    # return Parser.pure(lambda s: s.state_pos)
    return get_parser_state().and_then(lambda s: Parsec.pure(s.pos))


# -- | Returns the current input

# getInput :: (Monad m) => ParsecT s u m s
# getInput = do state <- getParserState
#               return (stateInput state)


def get_input() -> Parsec[Iterable[_T], _U, Iterable[_T]]:
    # return Parser.pure(lambda s: s.state_input)
    return get_parser_state().and_then(lambda s: Parsec.pure(s.input))


# -- | @setPosition pos@ sets the current source position to @pos@.

# setPosition :: (Monad m) => SourcePos -> ParsecT s u m ()
# setPosition pos
#     = do _ <- updateParserState (\(State input _ user) -> State input pos user)
#          return ()


def set_position(pos: SourcePos) -> Parsec[Iterable[_T], _U, None]:
    return update_parser_state(lambda s: State(s.input, pos, s.user_state)).then(
        Parsec.pure(None)
    )


# -- | @setInput input@ continues parsing with @input@. The 'getInput' and
# -- @setInput@ functions can for example be used to deal with #include
# -- files.

# setInput :: (Monad m) => s -> ParsecT s u m ()
# setInput input
#     = do _ <- updateParserState (\(State _ pos user) -> State input pos user)
#          return ()


def set_input(input: Iterable[_T]) -> Parsec[Iterable[_T], _U, None]:
    return update_parser_state(lambda s: State(input, s.pos, s.user_state)).then(
        Parsec.pure(None)
    )


# -- | Returns the full parser state as a 'State' record.

# getParserState :: (Monad m) => ParsecT s u m (State s u)
# getParserState = updateParserState id


def get_parser_state() -> Parsec[Iterable[_T], _U, State[Iterable[_T], _U]]:
    return update_parser_state(id)


# -- | @setParserState st@ set the full parser state to @st@.

# setParserState :: (Monad m) => State s u -> ParsecT s u m (State s u)
# setParserState st = updateParserState (const st)


def set_parser_state(
    st: State[Iterable[_T], _U],
) -> Parsec[Iterable[_T], _U, State[Iterable[_T], _U]]:
    return update_parser_state(lambda _: st)


# -- | @updateParserState f@ applies function @f@ to the parser state.

# updateParserState :: (State s u -> State s u) -> ParsecT s u m (State s u)
# updateParserState f =
#     ParsecT $ \s _ _ eok _ ->
#     let s' = f s
#     in eok s' s' $ unknownError s'


def update_parser_state(
    f: Callable[[State[Iterable[_T], _U]], State[Iterable[_T], _U]],
) -> Parsec[Iterable[_T], _U, State[Iterable[_T], _U]]:
    def _un_parser(
        s: State[Iterable[_T], _U],
        _0: Any,
        _1: Any,
        eok: Callable[
            [State[Iterable[_T], _U], State[Iterable[_T], _U], ParseError], Any
        ],
        _2: Any,
    ) -> Any:
        s_ = f(s)
        return eok(s_, s_, unknown_error(s))

    return Parsec(_un_parser)


# -- < User state combinators

# -- | Returns the current user state.

# getState :: (Monad m) => ParsecT s u m u
# getState = stateUser `liftM` getParserState


def get_state() -> Parsec[Iterable[_T], _U, _U]:
    return get_parser_state().and_then(lambda s: Parsec.pure(s.user_state))


# -- | @putState st@ set the user state to @st@.

# putState :: (Monad m) => u -> ParsecT s u m ()
# putState u = do _ <- updateParserState $ \s -> s { stateUser = u }
#                 return ()


def put_state(
    u: _U,
) -> Parsec[Iterable[_T], _U, None]:
    return update_parser_state(lambda s: State(s.input, s.pos, u)).then(
        Parsec.pure(None)
    )


# -- | @modifyState f@ applies function @f@ to the user state. Suppose
# -- that we want to count identifiers in a source, we could use the user
# -- state as:
# --
# -- >  expr  = do{ x <- identifier
# -- >            ; modifyState (+1)
# -- >            ; return (Id x)
# -- >            }

# modifyState :: (Monad m) => (u -> u) -> ParsecT s u m ()
# modifyState f = do _ <- updateParserState $ \s -> s { stateUser = f (stateUser s) }
#                    return ()


def modify_state(
    f: Callable[[_U], _U],
) -> Parsec[Iterable[_T], _U, None]:
    def _f(s: State[Iterable[_T], _U]) -> State[Iterable[_T], _U]:
        return State(s.input, s.pos, f(s.user_state))

    return update_parser_state(_f).then(Parsec.pure(None))


# -- XXX Compat

# -- | An alias for putState for backwards compatibility.

# setState :: (Monad m) => u -> ParsecT s u m ()
# setState = putState


def set_state(
    u: _U,
) -> Parsec[Iterable[_T], _U, None]:
    return put_state(u)


# -- | An alias for modifyState for backwards compatibility.

# updateState :: (Monad m) => (u -> u) -> ParsecT s u m ()
# updateState = modifyState


def update_state(
    f: Callable[[_U], _U],
) -> Parsec[Iterable[_T], _U, None]:
    return modify_state(f)


# -- | The parser @try p@ behaves like parser @p@, except that it
# -- pretends that it hasn't consumed any input when an error occurs.
# --
# -- This combinator is used whenever arbitrary look ahead is needed.
# -- Since it pretends that it hasn't consumed any input when @p@ fails,
# -- the ('<|>') combinator will try its second alternative even when the
# -- first parser failed while consuming input.
# --
# -- The @try@ combinator can for example be used to distinguish
# -- identifiers and reserved words. Both reserved words and identifiers
# -- are a sequence of letters. Whenever we expect a certain reserved
# -- word where we can also expect an identifier we have to use the @try@
# -- combinator. Suppose we write:
# --
# -- >  expr        = letExpr <|> identifier <?> "expression"
# -- >
# -- >  letExpr     = do{ string "let"; ... }
# -- >  identifier  = many1 letter
# --
# -- If the user writes \"lexical\", the parser fails with: @unexpected
# -- \'x\', expecting \'t\' in \"let\"@. Indeed, since the ('<|>') combinator
# -- only tries alternatives when the first alternative hasn't consumed
# -- input, the @identifier@ parser is never tried (because the prefix
# -- \"le\" of the @string \"let\"@ parser is already consumed). The
# -- right behaviour can be obtained by adding the @try@ combinator:
# --
# -- >  expr        = letExpr <|> identifier <?> "expression"
# -- >
# -- >  letExpr     = do{ try (string "let"); ... }
# -- >  identifier  = many1 letter

# try :: ParsecT s u m a -> ParsecT s u m a
# try p =
#     ParsecT $ \s cok _ eok eerr ->
#     unParser p s cok eerr eok eerr


def try_(p: Parsec[_S, _U, _A]) -> Parsec[_S, _U, _A]:
    def _un_parser(
        s: State[_S, _U],
        cok: Callable[[_A, State[_S, _U], ParseError], Any],
        _cerr: Callable[[ParseError], Any],
        eok: Callable[[_A, State[_S, _U], ParseError], Any],
        eerr: Callable[[ParseError], Any],
    ) -> Any:
        return p.un_parser(s, cok, eerr, eok, eerr)

    return Parsec(_un_parser)
