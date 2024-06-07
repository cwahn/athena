from ast import Call
from typing import Callable, Iterable, TypeVar

from entoli.base.maybe import Just, Maybe, Nothing
from entoli.parsec.prim import (
    ParseError,
    Parsec,
    SourcePos,
    SysUnExpect,
    UnExpect,
    many1,
    parse,
    skip_many,
    token_prim,
    try_,
    unexpected,
)
from entoli.prelude import append, foldr


_S = TypeVar("_S")
_U = TypeVar("_U")
_T = TypeVar("_T")
_V = TypeVar("_V")


# ! Convenience combinators
def some(p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, Iterable[_T]]:
    return p.some()


def _test_some():
    from entoli.parsec.char import char

    assert parse(some(char("a")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(some(char("a")), "", "a") == ["a"]
    assert parse(some(char("a")), "", "aa") == ["a", "a"]
    assert parse(some(char("a")), "", "b") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="b")]
    )


def many(p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, Iterable[_T]]:
    return p.many()


def _test_many():
    from entoli.parsec.char import char

    assert parse(many(char("a")), "", "") == []
    assert parse(many(char("a")), "", "a") == ["a"]
    assert parse(many(char("a")), "", "aa") == ["a", "a"]
    assert parse(many(char("a")), "", "b") == []


# -- | @choice ps@ tries to apply the parsers in the list @ps@ in order,
# -- until one of them succeeds. Returns the value of the succeeding
# -- parser.

# choice :: (Stream s m t) => [ParsecT s u m a] -> ParsecT s u m a
# {-# INLINABLE choice #-}
# choice ps           = foldr (<|>) mzero ps


def choice(ps: Iterable[Parsec[_S, _U, _T]]) -> Parsec[_S, _U, _T]:
    return foldr(lambda x, y: x.or_else(y), Parsec[_S, _U, _T].mzero(), ps)


def _test_choice():
    from entoli.parsec.char import char

    assert parse(choice([char("a"), char("b")]), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value=""), SysUnExpect(value="")]
    )
    assert parse(choice([char("a"), char("b")]), "", "a") == "a"
    assert parse(choice([char("a"), char("b")]), "", "b") == "b"
    assert parse(choice([char("a"), char("b")]), "", "c") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="c"), SysUnExpect(value="c")]
    )


# -- | @option x p@ tries to apply parser @p@. If @p@ fails without
# -- consuming input, it returns the value @x@, otherwise the value
# -- returned by @p@.
# --
# -- >  priority  = option 0 (do{ d <- digit
# -- >                          ; return (digitToInt d)
# -- >                          })

# option :: (Stream s m t) => a -> ParsecT s u m a -> ParsecT s u m a
# {-# INLINABLE option #-}
# option x p          = p <|> return x


def option(x: _T, p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, _T]:
    return p.or_else(Parsec[_S, _U, _T].pure(x))


def _test_option():
    from entoli.parsec.char import char

    assert parse(option("a", char("a")), "", "") == "a"
    assert parse(option("a", char("a")), "", "a") == "a"
    assert parse(option("a", char("a")), "", "b") == "a"
    assert parse(option("a", char("b")), "", "a") == "a"


# -- | @optionMaybe p@ tries to apply parser @p@.  If @p@ fails without
# -- consuming input, it return 'Nothing', otherwise it returns
# -- 'Just' the value returned by @p@.

# optionMaybe :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m (Maybe a)
# {-# INLINABLE optionMaybe #-}
# optionMaybe p       = option Nothing (liftM Just p)


def option_maybe(p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, Maybe[_T]]:
    return option(Nothing(), p.map(Just))


def _test_option_maybe():
    from entoli.parsec.char import char

    assert parse(option_maybe(char("a")), "", "") == Nothing()
    assert parse(option_maybe(char("a")), "", "a") == Just("a")
    assert parse(option_maybe(char("a")), "", "b") == Nothing()


# -- | @optional p@ tries to apply parser @p@.  It will parse @p@ or nothing.
# -- It only fails if @p@ fails after consuming input. It discards the result
# -- of @p@.

# optional :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m ()
# {-# INLINABLE optional #-}
# optional p          = do{ _ <- p; return ()} <|> return ()


def optional(
    p: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, None]:
    return p.map(lambda _: None).or_else(Parsec[_S, _U, None].pure(None))


def _test_optional():
    from entoli.parsec.char import char

    assert parse(optional(char("a")), "", "") is None
    assert parse(optional(char("a")), "", "a") is None
    assert parse(optional(char("a")), "", "b") is None
    # ! Need to add failing case


# -- | @between open close p@ parses @open@, followed by @p@ and @close@.
# -- Returns the value returned by @p@.
# --
# -- >  braces  = between (symbol "{") (symbol "}")

# between :: (Stream s m t) => ParsecT s u m open -> ParsecT s u m close
#             -> ParsecT s u m a -> ParsecT s u m a
# {-# INLINABLE between #-}
# between open close p
#                     = do{ _ <- open; x <- p; _ <- close; return x }


def between(
    open: Parsec[_S, _U, _T],
    close: Parsec[_S, _U, _T],
    p: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, _T]:
    return open.then(p).and_then(lambda x: close.then(Parsec[_S, _U, _T].pure(x)))


def _test_between():
    from entoli.parsec.char import char

    assert parse(between(char("["), char("]"), char("a")), "", "[a]") == "a"
    assert parse(between(char("["), char("]"), char("a")), "", "[b]") == ParseError(
        SourcePos("", 1, 2), [SysUnExpect(value="b")]
    )


# -- | @skipMany1 p@ applies the parser @p@ /one/ or more times, skipping
# -- its result.

# skipMany1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m ()
# {-# INLINABLE skipMany1 #-}
# skipMany1 p         = do{ _ <- p; skipMany p }
# {-
# skipMany p          = scan
#                     where
#                       scan  = do{ p; scan } <|> return ()
# -}


def skip_many1(p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, None]:
    return p.then(skip_many(p))


def _test_skip_many1():
    from entoli.parsec.char import char

    assert parse(skip_many1(char("a")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(skip_many1(char("a")), "", "a") is None
    assert parse(skip_many1(char("a")), "", "aa") is None
    assert parse(skip_many1(char("a")), "", "b") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="b")]
    )


# -- | @sepBy1 p sep@ parses /one/ or more occurrences of @p@, separated
# -- by @sep@. Returns a list of values returned by @p@.

# sepBy1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE sepBy1 #-}
# sepBy1 p sep        = do{ x <- p
#                         ; xs <- many (sep >> p)
#                         ; return (x:xs)
#                         }


# def sep_by1(
#     p: ParsecT[_S, _U, _T],
#     sep: ParsecT[_S, _U, _T],
# ) -> ParsecT[_S, _U, Iterable[_T]]:
#     return p.and_then(
#         lambda x: many(sep.then(p)).and_then(
#             lambda xs: ParsecT[_S, _U, Iterable[_T]].pure(append([x], xs))
#         )
#     )


def sep_by1(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _V],
) -> Parsec[_S, _U, Iterable[_T]]:
    return p.and_then(lambda x: many(sep.then(p)).map(lambda xs: append([x], xs)))


def _test_sep_by1():
    from entoli.parsec.char import char

    assert parse(sep_by1(char("a"), char(",")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(sep_by1(char("a"), char(",")), "", "a") == ["a"]
    assert parse(sep_by1(char("a"), char(",")), "", "a,a") == ["a", "a"]
    assert parse(sep_by1(char("a"), char(",")), "", "b") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="b")]
    )


# -- | @sepBy p sep@ parses /zero/ or more occurrences of @p@, separated
# -- by @sep@. Returns a list of values returned by @p@.
# --
# -- >  commaSep p  = p `sepBy` (symbol ",")

# sepBy :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE sepBy #-}
# sepBy p sep         = sepBy1 p sep <|> return []


def sep_by(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    return sep_by1(p, sep).or_else(Parsec[_S, _U, Iterable[_T]].pure([]))


def _test_sep_by():
    from entoli.parsec.char import char

    assert parse(sep_by(char("a"), char(",")), "", "") == []
    assert parse(sep_by(char("a"), char(",")), "", "a") == ["a"]
    assert parse(sep_by(char("a"), char(",")), "", "a,a") == ["a", "a"]
    assert parse(sep_by(char("a"), char(",")), "", "b") == []

    # -- | @sepEndBy p sep@ parses /zero/ or more occurrences of @p@,


# -- separated and optionally ended by @sep@, ie. haskell style
# -- statements. Returns a list of values returned by @p@.
# --
# -- >  haskellStatements  = haskellStatement `sepEndBy` semi

# sepEndBy :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE sepEndBy #-}
# sepEndBy p sep      = sepEndBy1 p sep <|> return []


def sep_end_by(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    return sep_end_by1(p, sep).or_else(Parsec[_S, _U, Iterable[_T]].pure([]))


def _test_sep_end_by():
    from entoli.parsec.char import char

    assert parse(sep_end_by(char("a"), char(",")), "", "") == []
    assert parse(sep_end_by(char("a"), char(",")), "", "a") == ["a"]
    assert parse(sep_end_by(char("a"), char(",")), "", "a,") == ["a"]
    assert parse(sep_end_by(char("a"), char(",")), "", "a,a") == ["a", "a"]
    assert parse(sep_end_by(char("a"), char(",")), "", "b") == []


# -- | @sepEndBy1 p sep@ parses /one/ or more occurrences of @p@,
# -- separated and optionally ended by @sep@. Returns a list of values
# -- returned by @p@.

# sepEndBy1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE sepEndBy1 #-}
# sepEndBy1 p sep     = do{ x <- p
#                         ; do{ _ <- sep
#                             ; xs <- sepEndBy p sep
#                             ; return (x:xs)
#                             }
#                           <|> return [x]
#                         }


def sep_end_by1(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    return p.and_then(
        lambda x: sep.then(
            sep_end_by(p, sep).and_then(
                lambda xs: Parsec[_S, _U, Iterable[_T]].pure(append([x], xs))
            )
        ).or_else(Parsec[_S, _U, Iterable[_T]].pure([x]))
    )


def _test_sep_end_by1():
    from entoli.parsec.char import char

    assert parse(sep_end_by1(char("a"), char(",")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(sep_end_by1(char("a"), char(",")), "", "a") == ["a"]
    assert parse(sep_end_by1(char("a"), char(",")), "", "a,") == ["a"]
    assert parse(sep_end_by1(char("a"), char(",")), "", "a,a") == ["a", "a"]
    assert parse(sep_end_by1(char("a"), char(",")), "", "b") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="b")]
    )


# -- | @endBy1 p sep@ parses /one/ or more occurrences of @p@, separated
# -- and ended by @sep@. Returns a list of values returned by @p@.

# endBy1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE endBy1 #-}
# endBy1 p sep        = many1 (do{ x <- p; _ <- sep; return x })


def end_by1(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    return many1(p.and_then(lambda x: sep.then(Parsec[_S, _U, _T].pure(x))))


def _test_end_by1():
    from entoli.parsec.char import char

    assert parse(end_by1(char("a"), char(",")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(end_by1(char("a"), char(",")), "", "a") == ParseError(
        SourcePos(name="", line=1, col=2), [SysUnExpect(value="")]
    )
    assert parse(end_by1(char("a"), char(",")), "", "a,") == ["a"]
    assert parse(end_by1(char("a"), char(",")), "", "a,a") == ParseError(
        SourcePos(name="", line=1, col=4), [SysUnExpect(value="")]
    )
    assert parse(end_by1(char("a"), char(",")), "", "b") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="b")]
    )


# -- | @endBy p sep@ parses /zero/ or more occurrences of @p@, separated
# -- and ended by @sep@. Returns a list of values returned by @p@.
# --
# -- >   cStatements  = cStatement `endBy` semi

# endBy :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m sep -> ParsecT s u m [a]
# {-# INLINABLE endBy #-}
# endBy p sep         = many (do{ x <- p; _ <- sep; return x })


def end_by(
    p: Parsec[_S, _U, _T],
    sep: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    return many(p.and_then(lambda x: sep.then(Parsec[_S, _U, _T].pure(x))))


def _test_end_by():
    from entoli.parsec.char import char

    assert parse(end_by(char("a"), char(",")), "", "") == []
    assert parse(end_by(char("a"), char(",")), "", "a") == ParseError(
        SourcePos(name="", line=1, col=2), [SysUnExpect(value="")]
    )
    assert parse(end_by(char("a"), char(",")), "", "a,") == ["a"]
    assert parse(end_by(char("a"), char(",")), "", "a,a") == ParseError(
        SourcePos(name="", line=1, col=4), [SysUnExpect(value="")]
    )
    assert parse(end_by(char("a"), char(",")), "", "b") == []


# -- | @count n p@ parses @n@ occurrences of @p@. If @n@ is smaller or
# -- equal to zero, the parser equals to @return []@. Returns a list of
# -- @n@ values returned by @p@.

# count :: (Stream s m t) => Int -> ParsecT s u m a -> ParsecT s u m [a]
# {-# INLINABLE count #-}
# count n p           | n <= 0    = return []
#                     | otherwise = sequence (replicate n p)

# todo Implement sequence, traverse


def count(
    n: int,
    p: Parsec[_S, _U, _T],
) -> Parsec[_S, _U, Iterable[_T]]:
    if n <= 0:
        return Parsec[_S, _U, Iterable[_T]].pure([])
    else:
        return foldr(
            lambda x, y: x.and_then(lambda x: y.map(lambda xs: append([x], xs))),
            Parsec[_S, _U, Iterable[_T]].pure([]),
            [p] * n,
        )


def _test_count():
    from entoli.parsec.char import char

    assert parse(count(0, char("a")), "", "") == []
    assert parse(count(1, char("a")), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(count(1, char("a")), "", "a") == ["a"]
    assert parse(count(2, char("a")), "", "a") == ParseError(
        SourcePos("", 1, 2), [SysUnExpect(value="")]
    )
    assert parse(count(2, char("a")), "", "aa") == ["a", "a"]
    assert parse(count(2, char("a")), "", "aaa") == ["a", "a"]


# -- | @chainr p op x@ parses /zero/ or more occurrences of @p@,
# -- separated by @op@ Returns a value obtained by a /right/ associative
# -- application of all functions returned by @op@ to the values returned
# -- by @p@. If there are no occurrences of @p@, the value @x@ is
# -- returned.

# chainr :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m (a -> a -> a) -> a -> ParsecT s u m a
# {-# INLINABLE chainr #-}
# chainr p op x       = chainr1 p op <|> return x


def chainr(
    p: Parsec[_S, _U, _T],
    op: Parsec[_S, _U, Callable[[_T, _T], _T]],
    x: _T,
) -> Parsec[_S, _U, _T]:
    return chainr1(p, op).or_else(Parsec[_S, _U, _T].pure(x))


# -- | @chainl p op x@ parses /zero/ or more occurrences of @p@,
# -- separated by @op@. Returns a value obtained by a /left/ associative
# -- application of all functions returned by @op@ to the values returned
# -- by @p@. If there are zero occurrences of @p@, the value @x@ is
# -- returned.

# chainl :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m (a -> a -> a) -> a -> ParsecT s u m a
# {-# INLINABLE chainl #-}
# chainl p op x       = chainl1 p op <|> return x


def chainl(
    p: Parsec[_S, _U, _T],
    op: Parsec[_S, _U, Callable[[_T, _T], _T]],
    x: _T,
) -> Parsec[_S, _U, _T]:
    return chainl1(p, op).or_else(Parsec[_S, _U, _T].pure(x))


def _test_chainl():
    from entoli.parsec.char import char

    p = char("1").map(int)
    op = char("+").map(lambda _: lambda x, y: x + y)

    assert parse(chainl(p, op, 9), "", "") == 9
    assert parse(chainl(p, op, 9), "", "1") == 1
    assert parse(chainl(p, op, 9), "", "1+1") == 2
    assert parse(chainl(p, op, 9), "", "1+1+1") == 3


# -- | @chainl1 p op@ parses /one/ or more occurrences of @p@,
# -- separated by @op@ Returns a value obtained by a /left/ associative
# -- application of all functions returned by @op@ to the values returned
# -- by @p@. This parser can for example be used to eliminate left
# -- recursion which typically occurs in expression grammars.
# --
# -- >  expr    = term   `chainl1` addop
# -- >  term    = factor `chainl1` mulop
# -- >  factor  = parens expr <|> integer
# -- >
# -- >  mulop   =   do{ symbol "*"; return (*)   }
# -- >          <|> do{ symbol "/"; return (div) }
# -- >
# -- >  addop   =   do{ symbol "+"; return (+) }
# -- >          <|> do{ symbol "-"; return (-) }

# chainl1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m (a -> a -> a) -> ParsecT s u m a
# {-# INLINABLE chainl1 #-}
# chainl1 p op        = do{ x <- p; rest x }
#                     where
#                       rest x    = do{ f <- op
#                                     ; y <- p
#                                     ; rest (f x y)
#                                     }
#                                 <|> return x


def chainl1(
    p: Parsec[_S, _U, _T],
    op: Parsec[_S, _U, Callable[[_T, _T], _T]],
) -> Parsec[_S, _U, _T]:
    def rest(x: _T) -> Parsec[_S, _U, _T]:
        return op.and_then(lambda f: p.and_then(lambda y: rest(f(x, y)))).or_else(
            Parsec[_S, _U, _T].pure(x)
        )

    return p.and_then(rest)


def _test_chain1():
    from entoli.parsec.char import char

    p = char("1").map(int)
    op = char("+").map(lambda _: lambda x, y: x + y)

    assert parse(chainl1(p, op), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(chainl1(p, op), "", "1") == 1
    assert parse(chainl1(p, op), "", "1+1") == 2
    assert parse(chainl1(p, op), "", "1+1+1") == 3


# -- | @chainr1 p op x@ parses /one/ or more occurrences of |p|,
# -- separated by @op@ Returns a value obtained by a /right/ associative
# -- application of all functions returned by @op@ to the values returned
# -- by @p@.

# chainr1 :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m (a -> a -> a) -> ParsecT s u m a
# {-# INLINABLE chainr1 #-}
# chainr1 p op        = scan
#                     where
#                       scan      = do{ x <- p; rest x }

#                       rest x    = do{ f <- op
#                                     ; y <- scan
#                                     ; return (f x y)
#                                     }
#                                 <|> return x


def chainr1(
    p: Parsec[_S, _U, _T],
    op: Parsec[_S, _U, Callable[[_T, _T], _T]],
) -> Parsec[_S, _U, _T]:
    def scan() -> Parsec[_S, _U, _T]:
        def rest(x: _T) -> Parsec[_S, _U, _T]:
            return op.and_then(lambda f: scan().map(lambda y: f(x, y))).or_else(
                Parsec[_S, _U, _T].pure(x)
            )

        return p.and_then(rest)

    return scan()


def _test_chainr1():
    from entoli.parsec.char import char

    p = char("1").map(int)
    op = char("+").map(lambda _: lambda x, y: x + y)

    assert parse(chainr1(p, op), "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(chainr1(p, op), "", "1") == 1
    assert parse(chainr1(p, op), "", "1+1") == 2
    assert parse(chainr1(p, op), "", "1+1+1") == 3


# -----------------------------------------------------------
# -- Tricky combinators
# -----------------------------------------------------------
# -- | The parser @anyToken@ accepts any kind of token. It is for example
# -- used to implement 'eof'. Returns the accepted token.

# anyToken :: (Stream s m t, Show t) => ParsecT s u m t
# {-# INLINABLE anyToken #-}
# anyToken            = tokenPrim show (\pos _tok _toks -> pos) Just

any_token = token_prim(
    str,
    lambda pos, tok, toks: pos,
    Just,
)


def _test_any_token():
    assert parse(any_token, "", "") == ParseError(
        SourcePos("", 1, 1), [SysUnExpect(value="")]
    )
    assert parse(any_token, "", "a") == "a"
    assert parse(any_token, "", "aa") == "a"


# -- | @notFollowedBy p@ only succeeds when parser @p@ fails. This parser
# -- does not consume any input. This parser can be used to implement the
# -- \'longest match\' rule. For example, when recognizing keywords (for
# -- example @let@), we want to make sure that a keyword is not followed
# -- by a legal identifier character, in which case the keyword is
# -- actually an identifier (for example @lets@). We can program this
# -- behaviour as follows:
# --
# -- >  keywordLet  = try (do{ string "let"
# -- >                       ; notFollowedBy alphaNum
# -- >                       })
# --
# -- __NOTE__: Currently, 'notFollowedBy' exhibits surprising behaviour
# -- when applied to a parser @p@ that doesn't consume any input;
# -- specifically
# --
# --  - @'notFollowedBy' . 'notFollowedBy'@ is /not/ equivalent to 'lookAhead', and
# --
# --  - @'notFollowedBy' 'eof'@ /never/ fails.
# --
# -- See [haskell/parsec#8](https://github.com/haskell/parsec/issues/8)
# -- for more details.

# notFollowedBy :: (Stream s m t, Show a) => ParsecT s u m a -> ParsecT s u m ()
# {-# INLINABLE notFollowedBy #-}
# notFollowedBy p     = try (do{ c <- try p; unexpected (show c) }
#                            <|> return ()
#                           )


def not_followed_by(p: Parsec[_S, _U, _T]) -> Parsec[_S, _U, None]:
    return try_(
        try_(p)
        .and_then(lambda c: unexpected(str(c)))
        .or_else(Parsec[_S, _U, None].pure(None))
    )


def _test_not_followed_by():
    from entoli.parsec.char import char

    assert parse(not_followed_by(char("a")), "", "") is None
    assert parse(not_followed_by(char("a")), "", "a") == ParseError(
        SourcePos("", 1, 2), [UnExpect(value="a")]
    )
    assert parse(not_followed_by(char("a")), "", "b") is None
    assert parse(not_followed_by(char("a")), "", "aa") == ParseError(
        SourcePos("", 1, 2), [UnExpect(value="a")]
    )
    assert parse(not_followed_by(char("a")), "", "ab") == ParseError(
        SourcePos("", 1, 2), [UnExpect(value="a")]
    )


# -- | This parser only succeeds at the end of the input. This is not a
# -- primitive parser but it is defined using 'notFollowedBy'.
# --
# -- >  eof  = notFollowedBy anyToken <?> "end of input"

# eof :: (Stream s m t, Show t) => ParsecT s u m ()
# {-# INLINABLE eof #-}
# eof                 = notFollowedBy anyToken <?> "end of input"

eof = not_followed_by(any_token)


def _test_eof():
    assert parse(eof, "", "") is None
    assert parse(eof, "", "a") == ParseError(SourcePos("", 1, 1), [UnExpect(value="a")])


# -- | @manyTill p end@ applies parser @p@ /zero/ or more times until
# -- parser @end@ succeeds. Returns the list of values returned by @p@.
# -- This parser can be used to scan comments:
# --
# -- >  simpleComment   = do{ string "<!--"
# -- >                      ; manyTill anyChar (try (string "-->"))
# -- >                      }
# --
# --    Note the overlapping parsers @anyChar@ and @string \"-->\"@, and
# --    therefore the use of the 'try' combinator.

# manyTill :: (Stream s m t) => ParsecT s u m a -> ParsecT s u m end -> ParsecT s u m [a]
# {-# INLINABLE manyTill #-}
# manyTill p end      = scan
#                     where
#                       scan  = do{ _ <- end; return [] }
#                             <|>
#                               do{ x <- p; xs <- scan; return (x:xs) }


def many_till(
    p: Parsec[_S, _U, _T],
    end: Parsec[_S, _U, _V],
) -> Parsec[_S, _U, Iterable[_T]]:
    def scan() -> Parsec[_S, _U, Iterable[_T]]:
        return end.then(Parsec[_S, _U, Iterable[_T]].pure([])).or_else(
            p.and_then(
                lambda x: scan().and_then(
                    lambda xs: Parsec[_S, _U, Iterable[_T]].pure(append([x], xs))
                )
            )
        )

    return scan()


def _test_many_till():
    from entoli.parsec.char import char

    assert parse(many_till(char("a"), char("b")), "", "") == ParseError(
        SourcePos("", 1, 1),
        [SysUnExpect(""), SysUnExpect("")],
    )
    assert parse(many_till(char("a"), char("b")), "", "a") == ParseError(
        SourcePos("", 1, 2),
        [SysUnExpect(""), SysUnExpect("")],
    )
    assert parse(many_till(char("a"), char("b")), "", "b") == []
    assert parse(many_till(char("a"), char("b")), "", "ab") == ["a"]
    assert parse(many_till(char("a"), char("b")), "", "aab") == ["a", "a"]
    assert parse(many_till(char("a"), char("b")), "", "aaab") == ["a", "a", "a"]


# -- | @parserTrace label@ is an impure function, implemented with "Debug.Trace" that
# -- prints to the console the remaining parser state at the time it is invoked.
# -- It is intended to be used for debugging parsers by inspecting their intermediate states.
# --
# -- > *> parseTest (oneOf "aeiou"  >> parserTrace "label") "atest"
# -- > label: "test"
# -- > ...
# --
# -- @since 3.1.12.0
# parserTrace :: (Show t, Stream s m t) => String -> ParsecT s u m ()
# {-# INLINABLE parserTrace #-}
# parserTrace s = pt <|> return ()
#     where
#         pt = try $ do
#            x <- try $ many1 anyToken
#            trace (s++": " ++ show x) $ try $ eof
#            fail (show x)

# -- | @parserTraced label p@ is an impure function, implemented with "Debug.Trace" that
# -- prints to the console the remaining parser state at the time it is invoked.
# -- It then continues to apply parser @p@, and if @p@ fails will indicate that
# -- the label has been backtracked.
# -- It is intended to be used for debugging parsers by inspecting their intermediate states.
# --
# -- > *>  parseTest (oneOf "aeiou"  >> parserTraced "label" (oneOf "nope")) "atest"
# -- > label: "test"
# -- > label backtracked
# -- > parse error at (line 1, column 2):
# -- > ...
# --
# -- @since 3.1.12.0
# parserTraced :: (Stream s m t, Show t) => String -> ParsecT s u m b -> ParsecT s u m b
# {-# INLINABLE parserTraced #-}
# parserTraced s p = do
#   parserTrace s
#   p <|> trace (s ++ " backtracked") (fail s)
