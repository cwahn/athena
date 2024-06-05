from typing import Callable, List, Tuple, TypeVar, Generic, Union

T = TypeVar('T')
U = TypeVar('U')

class Parser(Generic[T]):
    def __init__(self, parse: Callable[[str], Tuple[str, T]]):
        self.parse = parse

    def __call__(self, input: str) -> Tuple[str, T]:
        return self.parse(input)

    def __or__(self, other: 'Parser[T]') -> 'Parser[T]':
        def parse(input: str) -> Tuple[str, T]:
            try:
                return self.parse(input)
            except:
                return other.parse(input)
        return Parser(parse)

    def map(self, func: Callable[[T], U]) -> 'Parser[U]':
        def parse(input: str) -> Tuple[str, U]:
            rest, result = self.parse(input)
            return rest, func(result)
        return Parser(parse)

    def and_then(self, other: 'Parser[U]') -> 'Parser[Tuple[T, U]]':
        def parse(input: str) -> Tuple[str, Tuple[T, U]]:
            rest, result1 = self.parse(input)
            rest, result2 = other.parse(rest)
            return rest, (result1, result2)
        return Parser(parse)

def pure(value: T) -> Parser[T]:
    return Parser(lambda input: (input, value))

def some(v: Parser[T]) -> Parser[List[T]]:
    def some_v() -> Parser[List[T]]:
        return v.and_then(lazy_many_v()).map(lambda t: [t[0]] + t[1])

    def lazy_many_v() -> Parser[List[T]]:
        return Parser(lambda input: many_v()(input))

    def many_v() -> Parser[List[T]]:
        return some_v() | pure([])

    return some_v()

def many(v: Parser[T]) -> Parser[List[T]]:
    def some_v() -> Parser[List[T]]:
        return v.and_then(lazy_many_v()).map(lambda t: [t[0]] + t[1])

    def lazy_many_v() -> Parser[List[T]]:
        return Parser(lambda input: many_v()(input))

    def many_v() -> Parser[List[T]]:
        return some_v() | pure([])

    return many_v()

# Example usage
def char_parser(c: str) -> Parser[str]:
    def parse(input: str) -> Tuple[str, str]:
        if input and input[0] == c:
            return input[1:], c
        else:
            raise Exception(f"Expected {c}")
    return Parser(parse)

a_parser = char_parser('a')

# Parse one or more 'a's
some_a_parser = some(a_parser)

# Parse zero or more 'a's
many_a_parser = many(a_parser)

print(some_a_parser("aaab"))  # Output: ('b', ['a', 'a', 'a'])
print(many_a_parser("aaab"))  # Output: ('b', ['a', 'a', 'a'])
print(many_a_parser("b"))     # Output: ('b', [])
