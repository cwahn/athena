# def sum_type(cls):
#     # Make it as definition of sum_type

#     member_constructors = [
#         member for member in cls.__dict__.values() if isinstance(member, type)
#     ]


# @sum_type
# class Shape:
#     class Circle:
#         radius: float

#     class Rectangle:
#         width: float
#         height: float


# some_shape = Shape.Circle(1.0)


from dataclasses import dataclass
import math


type Shape = Circle | Rectangle


@dataclass
class Circle:
    radius: float


@dataclass
class Rectangle:
    width: float
    height: float


# A function taking Shape as an argument
def area(shape: Shape) -> float:
    match shape:
        case Circle(radius):
            return math.pi * radius**2
        case Rectangle(width, height):
            return width * height
