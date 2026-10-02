"""
@file path_node.py
@brief PathNode class implementation for laser scriber path planning.

@author Matthew Fox
@date 2025-02-11
@version 1.0

This file contains the implementation of the PathNode class, which models a node in 
a path that a laser scriber is meant to follow.
"""
# Local module imports
from .point import Point


class PathNode:
    _pos: Point
    _beam_state: bool
    _approach_speed: float
    _line_type: str
    _approach_angle: float

    # This class models a node in a path a laser scriber is meant to follow. 
    # The node has position, and what the angle and beam state should be on approach.

    #region Constructors
    def __init__(self, pos: Point, beam_state: bool, approach_speed: float, line_type: str, approach_angle: float = 0) -> None:
        """
        Initialize a PathNode object with a point.
        
        :param pos: The (x, y) position of the node.
        :param beam_state: The current beam state of the node on approach.
        :param approach_angle: The angle of the approach towards the node.
        :rtype: object
        """
        self._pos = pos
        self._beam_state = beam_state
        self._approach_speed = approach_speed
        self._line_type = line_type
        self._approach_angle = approach_angle

    #endregion

    #region Getters/Properties
    @property
    def pos(self) -> Point:
        """
        Get the (x, y) position of the node.
        
        :rtype: Point
        :return: The (x, y) position of the node.
        """
        return self._pos

    @property
    def beam_state(self) -> bool:
        """
        Get the current beam state of the node on approach.
        
        :rtype: bool
        :return: True if the beam is on towards the node, False otherwise.
        """
        return self._beam_state
    
    @property
    def approach_speed(self) -> float:
        """
        Gets the speed on approach towards the node.

        :rtype: float
        :return: The speed of approach towards the node.
        """
        return self._approach_speed
    
    @property
    def line_type(self) -> str:
        """
        Gets the type of the line on approach.

        :rtype: str
        :return: The type of the line on approach.
        """
        return self._line_type

    @property
    def approach_angle(self) -> float:
        """
        Gets the angle of the approach towards the node.
        
        :rtype: float
        :return: The angle of the approach towards the node.
        """
        return self._approach_angle

    #endregion

    #region Setters
    @pos.setter
    def pos(self, pos: Point) -> None:
        """
        Set the position of the node.
        
        :rtype: None
        :param pos: The (x, y) position of the node.
        """
        self._pos = pos

    @beam_state.setter
    def beam_state(self, beam_state: bool) -> None:
        """
        Set whether the node's beam is active or not.
        
        :rtype: None
        :param beam_state: The current beam state of the node on approach.
        """
        self._beam_state = beam_state
    
    @approach_speed.setter
    def approach_speed(self, approach_speed: float) -> None:
        """
        Set the speed on approach towards the node.

        :rtype: None
        :param approach_speed: The speed of approach towards the node.
        """
        self._approach_speed = approach_speed
    
    @line_type.setter
    def line_type(self, line_type: str) -> None:
        """
        Set the line type on approach towards the node.

        :rtype: None
        :param line_type: The line type of approach towards the node.
        """
        self._line_type = line_type

    @approach_angle.setter
    def approach_angle(self, angle_of_approach: float) -> None:
        """
        Set the angle at which the node is approached.
        
        :rtype: None
        :param angle_of_approach: The angle of the approach towards the node.
        """
        self._approach_angle = angle_of_approach

    #endregion
    
    #region Equality
    def __eq__(self, other: object) -> bool:
        """
        :rtype: bool
        :param other: Another object to test.
        :return: True if the attributes of each PathNode are equivalent.
        """
        if not isinstance(other, PathNode):
            return NotImplemented
        return (
            self.pos == other.pos 
            and self.beam_state == other.beam_state 
            and self.approach_speed == other.approach_speed
            and self.line_type == other.line_type
            and self.approach_angle == other.approach_angle
        )
    
    def __ne__(self, other: object) -> bool:
        """
        :rtype: bool
        :param other: Another object to test.
        :return: True if the attributes of each PathNode are not equivalent.
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
    
    #endregion

    #region toString
    def __repr__(self) -> str:
        """
        Return a string representation of the PathNode object.
        
        :rtype: str
        :return: The position, beam state, and angle of approach as a string.
        """
        return "PathNode(Position: ({}, {}), Beam State: {}, Speed on Approach: {}, Line Type: {}, Angle of Approach: {}°)".format(
            self.pos.x, 
            self.pos.y, 
            "On" if self.beam_state else "Off",
            self.approach_speed,
            self.line_type,
            self.approach_angle
        )

    #endregion