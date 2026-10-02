"""
@file point.py
@brief Point class implementation for holding x, y coordinates.

@author Matthew Fox
@date 2025-02-12
@version 1.0

This file contains an implementation of a point class, which models a cartesian coordinate.
"""


class Point:
    _x: float
    _y: float

    # This class models a cartesian coordinate, providing algebraic operation helper functions.
    
    #region Constructors
    def __init__(self, x: float, y: float) -> None:
        self._x = x
        self._y = y

    #endregion
    
    #region Getters
    @property
    def x(self) -> float:
        """
        :rtype: float
        :return: The x coordinate of the point.
        """
        return self._x
    
    @property
    def y(self) -> float:
        """
        :rtype: float
        :return: The y coordinate of the point.
        """
        return self._y

    #endregion
    
    #region Setters
    @x.setter
    def x(self, x: float) -> None:
        """
        :rtype: None
        :param x: The x coordinate of the point.
        """
        if x is None:
            raise ValueError("x cannot be None")
        if not isinstance(x, float):
            raise TypeError("x must be a float.")
        if float(x) != x:
            raise ValueError("x must be a float.")
        self._x = x
    
    @y.setter
    def y(self, y: float) -> None:
        """
        :rtype: None
        :param y: The y coordinate of the point.
        """
        if y is None:
            raise ValueError("y cannot be None")
        if not isinstance(y, float):
            raise TypeError("y must be a float.")
        if float(y) != y:
            raise ValueError("y must be a float.")
        self._y = y

    #endregion
    
    #region Methods
    def translate(self, dx: float = 0, dy: float = 0) -> "Point":
        """
        Translate the point by a given amount.
        
        :param dx: The change in x coordinate.
        :param dy: The change in y coordinate.
        :rtype: "Point"
        :return: The translated point.
        """
        x = self._x + dx
        y = self._y + dy
        return Point(x, y)

    #endregion

    #region Copy
    def __copy__(self) -> "Point":
        """
        :rtype: "Point"
        :return: A copy of this point. 
        """
        return Point(self._x, self._y)

    #endregion
    
    #region Equality
    def __eq__(self, other: object) -> bool:
        """
        :rtype: bool
        :param other: Another object to test.
        :return: True if the coordinates of each point are equivalent.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other: object) -> bool:
        """
        :rtype: bool
        :param other: Another object to test.
        :return: True if the coordinates of each point are not equivalent.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    #endregion
    
    #region Rounding and Casting
    def __round__(self, n: int = 0) -> "Point":
        """
        Rounds this point to the given number of decimal places.

        :param n: The number of decimal places.
        :rtype: "Point"
        :return: The point with its components rounded.
        """
        return Point(round(self._x, n), round(self._y, n))
    
    def to_int(self) -> "Point":
        """
        :return: This point with its components cast to integers.
        :rtype: "Point"
        """
        return Point(int(self._x), int(self._y))
    
    def to_float(self) -> "Point":
        """
        :return: This point with its components cast to floats.
        :rtype: "Point"
        """
        return Point(float(self._x), float(self._y))
    
    #endregion

    #region Algebraic Operations
    def __abs__(self) -> "Point":
        """
        :rtype: "Point"
        """
        return Point(abs(self.x), abs(self.y))
    
    def __add__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x - other.x, self.y - other.y)
    
    def __mul__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x * other.x, self.y * other.y)
    
    def __truediv__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x / other.x, self.y / other.y)
    
    def __floordiv__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x // other.x, self.y // other.y)
    
    def __mod__(self, other: "Point") -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x % other.x, self.y % other.y)
    
    def __pow__(self, power, modulo=None) -> "Point":
        """
        :rtype: "Point"
        """
        return Point(self.x ** power.x, self.y ** power.y)

    #endregion

    #region toString
    def __str__(self) -> str:
        """
        :rtype: str
        """
        return f"({self.x}, {self.y})"

    def __repr__(self) -> str:
        """
        :rtype: str
        """
        return f"Point({self.x}, {self.y})"

    #endregion