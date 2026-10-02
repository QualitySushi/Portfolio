#region Comments Legend

# ! Red for Bus bars
# ? Orange
# // Grey for Consistent or essential
# todo Aqua for todos
# % Blue for cells
# * Green for Isolation Lines
# @ Purple for Decision
# regions are brown, as well as
# endregions

#endregion

#region Imports
# Standard imports
import logging
import math
from typing import Literal

import numpy as np

# Local imports
from core.path_node import PathNode
from core.point import Point
from core.solar_data import CellParameters, LaserData, P1Specific, P2Specific

#endregion

#region Literals
# Line types for Matplotlib visualization color changing on the front end.
_LINE_TYPES = Literal["isolation", "cell", "bus_bar"]

# Degrees or Radians for rotation.
_ANGLE_UNITS = Literal["degrees", "radians"]

# Start possibilities for point path options.
_START_POSITIONS = Literal[
    "top_left",
    "bottom_left",
    "top_right",
    "bottom_right",
    "middle_left",
    "middle_right"
]

# The directions in which to move for scribe generation based on start position.
_START_DIRECTIONS: dict[
    str, dict[str, int]] = {
    "top_left": {"x_direction": 1, "y_direction": -1},
    "bottom_left": {"x_direction": 1, "y_direction": 1},
    "top_right": {"x_direction": -1, "y_direction": -1},
    "bottom_right": {"x_direction": -1, "y_direction": 1},
    "middle_left": {"x_direction": 1, "y_direction": 1},
    "middle_right": {"x_direction": -1, "y_direction": 1}
}
#endregion


def compute_cell_width(
        cell_count: int,
        panel_max_size: float,
        is_p1: bool,
        bus_bar_width: float = 0.0,
        p2_bus_spacing: float = 0.0,
        bus_bar_spacing: float = 0.0,
        edge_margin: float = 0.0,
        resolution: float = 0.001
) -> float:
    """
    Derives the widest cell width that keeps the whole configuration on the panel for a given cell count.

    The cell array is centered on the panel. Every side keeps `edge_margin` clear of scribes (the deleted border). P1
    has no bus bars, so the array may fill the rest of the panel. P2 places a bus bar before the first cell and after
    the last one, each `clearance + bus_bar_width` beyond the array, so the space on both sides must hold the larger
    of the two.

    :param cell_count: The number of cells.
    :param panel_max_size: The size of the square panel.
    :param is_p1: True for a P1 scribe, False for P2.
    :param bus_bar_width: The width of a bus bar (P2 only).
    :param p2_bus_spacing: The clearance before the first cell to the first bus bar (P2 only).
    :param bus_bar_spacing: The clearance after the last cell to the second bus bar (P2 only).
    :param edge_margin: The border kept clear of scribes on every side of the panel.
    :param resolution: The width is rounded DOWN to a multiple of this, so count * width never exceeds the space.
    :rtype: float.
    :return: The cell width.
    """
    if cell_count < 1:
        raise ValueError("At least one cell is required.")

    if edge_margin < 0:
        raise ValueError("The edge margin cannot be negative.")

    bus_bar_clearance: float = 0.0 if is_p1 else max(p2_bus_spacing, bus_bar_spacing) + bus_bar_width
    edge_clearance: float = edge_margin + bus_bar_clearance
    available_span: float = panel_max_size - 2 * edge_clearance
    if available_span <= 0:
        raise ValueError(
            f"The edge margin ({edge_margin} mm) and bus bars ({bus_bar_clearance} mm) take "
            f"{edge_clearance} mm on each side, which leaves no room on a {panel_max_size} mm panel. "
            f"Reduce the edge margin, bus bar clearance or bus bar width."
        )

    cell_width: float = round(math.floor(available_span / cell_count / resolution) * resolution, 6)
    if cell_width <= 0:
        raise ValueError(f"{cell_count} cells do not fit in {available_span} mm.")
    return cell_width


class PathGenerator:
    """
    Class to generate a scribing path for a CNC laser from solar cell parameters.
    
    Attributes:
        _cell_parameters: CellParameters: The cell width, height, and quantity.
        _p1_specific: P1Specific: The spacing of isolation lines.
        _p2_specific: P2Specific: The offset between scribing passes, the width of a scribe, and the spacing 
            between bus bars.
        _laser_data: LaserData: The Speed of the laser, and if the scribe is p1 or p2.
        _rotation: float: The angle in degrees or radians to rotate the path for alignment.
        _panel_size: float: The size of a square solar panel.
        _path: list: The generated path: The path made from the generator as output.
        _isolation_line_offset: float: The offset of the edges of the isolation lines from the edges of the p1 cells.
        _isolation_line_length: float: The length of the isolation lines.
        _midpoint: Point: The midpoint of the scribe, for rotation.
        _debug_mode: bool: True when the code is executed from an IDE or terminal, False if run from a packaged 
            application.
    """
    #region Attributes
    _cell_parameters: CellParameters
    _p1_specific: P1Specific
    _p2_specific: P2Specific
    _laser_data: LaserData
    _rotation: np.float64
    _panel_size: float
    _path: list[PathNode]
    _isolation_line_offset: float
    _isolation_line_length: float
    _midpoint: Point
    _debug_mode: bool
    _edge_margin: float
    #endregion

    #region Constructors
    def __init__(
            self,
            cell_parameters: CellParameters,
            p1_specific: P1Specific,
            p2_specific: P2Specific,
            laser_data: LaserData,
            rotation: np.float64,
            panel_max_size: float,
            debug_mode: bool,
            edge_margin: float = 0.0
    ):
        """
        Initialize path generator with the cell parameters, laser data, and the origin.
        
        Args:
            :param cell_parameters: CellParameters: The cell width, height, and quantity.
            :param p1_specific: P1Specific: The spacing of isolation lines.
            :param p2_specific: P2Specific: The offset between scribing passes, the width of a scribe, and the spacing 
                between bus bars.
            :param laser_data: LaserData: The Speed of the laser, and if the scribe is p1 or p2.
            :param rotation: np.float64: The angle in degrees or radians to rotate the path for alignment.
            :param panel_max_size: float: The size of a square solar panel.
            :param debug_mode: bool: True when the code is executed from an IDE or terminal, False if run from a 
                packaged application.
            :param edge_margin: float: The border kept clear of scribes on every side of the panel, in mm.
        """
        # Parameters
        self._cell_parameters = cell_parameters
        self._p1_specific = p1_specific
        self._p2_specific = p2_specific
        self._laser_data = laser_data
        self._rotation = rotation
        self._panel_size = panel_max_size
        self._debug_mode = debug_mode
        self._edge_margin = edge_margin

        #region Logging Setup
        # Set logging behavior based on debug mode condition.
        if self._debug_mode:
            # Configure logging
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s - %(levelname)s - %(message)s',
                                filename='path_generator_debug.log',
                                filemode='w'
                                )
            self._logger = logging.getLogger(__name__)

            # Add console handler to see logs in real-time
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            console.setFormatter(formatter)
            self._logger.addHandler(console)
        #endregion

        # Log all input parameters.
        # if self._debug_mode:
        #     self._logger.debug("=== Initializing PathGenerator ===")
        #     self._logger.debug(
        #         f"Cell Parameters: width={self._cell_parameters.cell_width}, length={self._cell_parameters.cell_length}"
        #         f", count={self._cell_parameters.cell_count}"
        #     )
        #     self._logger.debug(f"Origin: x={self._cell_parameters.origin.x}, y={self._cell_parameters.origin.y}")
        #     self._logger.debug(f"P1 Specific: isolation_line_spacing={self._p1_specific.isolation_line_spacing}")
        #     self._logger.debug(
        #         f"P2 Specific: pass_gap={self._p2_specific.pass_gap}, pass_count={self._p2_specific.pass_count}"
        #         f", bus_bar_width={self._p2_specific.bus_bar_width}"
        #     )
        #     self._logger.debug(
        #         f"Laser Data: is_p1={self._laser_data.is_p1}, translation_speed={self._laser_data.translation_speed}"
        #         f", scribing_speed={self._laser_data.scribing_speed}"
        #     )
        #     self._logger.debug(f"Rotation: {self._rotation} degrees")
        #     self._logger.debug(f"Panel Size: {self._panel_size}")
        #     self._logger.debug(f"Edge Margin: {self._edge_margin}")

        # The cell width is derived from the cell count so the configuration always fits the panel. Any cell width
        # sent by the caller is ignored.
        self._cell_parameters.cell_width = compute_cell_width(
            cell_count=self._cell_parameters.cell_count,
            panel_max_size=self._panel_size,
            is_p1=self._laser_data.is_p1,
            bus_bar_width=self._p2_specific.bus_bar_width,
            p2_bus_spacing=self._p2_specific.p2_bus_spacing,
            bus_bar_spacing=self._p2_specific.bus_bar_spacing,
            edge_margin=self._edge_margin
        )

        # Validate that the cells fit on the panel. Otherwise the isolation line offset below goes negative and the
        # whole path is shifted off the panel.
        cell_span: float = self._cell_parameters.cell_count * self._cell_parameters.cell_width
        if cell_span > self._panel_size + 1e-9:
            raise ValueError(
                f"{self._cell_parameters.cell_count} cells x {self._cell_parameters.cell_width} mm = {cell_span} mm, "
                f"which exceeds the panel size of {self._panel_size} mm. Reduce the cell count or cell width."
            )

        # Validate that the scribe lines fit on the panel inside the edge margins.
        max_cell_length: float = self._panel_size - 2 * self._edge_margin
        if not 0 < self._cell_parameters.cell_length <= max_cell_length + 1e-9:
            raise ValueError(
                f"Cell length of {self._cell_parameters.cell_length} mm must be greater than 0 and no more than "
                f"{max_cell_length} mm (the {self._panel_size} mm panel minus two {self._edge_margin} mm edge margins)."
            )

        # Attributes
        
        # Initialize the path.
        self._path: list[PathNode] = []
        
        # Find the offset between the cells and the isolation lines.
        # Original calculation =(300-17*6.7)/2
        self._isolation_line_offset: float = ((self._panel_size
                                               - (self._cell_parameters.cell_count * self._cell_parameters.cell_width))
                                              / 2)
        # The length of an isolation line.
        self._isolation_line_length: float = ((self._cell_parameters.cell_width
                                               * self._cell_parameters.cell_count)
                                              + (self._isolation_line_offset * 2))

        # if self._debug_mode:
        #     self._logger.debug(f"Calculated isolation_line_offset: {self._isolation_line_offset}")
        #     self._logger.debug(f"Initial isolation_line_length: {self._isolation_line_length}")

        # Clamp the isolation line length to the size of the panel if it's too long.
        if self._cell_parameters.origin.y + self._isolation_line_length > self._panel_size:
            self._isolation_line_length = self._panel_size - self._cell_parameters.origin.y * 2
            # if self._debug_mode:
            #     self._logger.debug(f"Adjusted isolation_line_length (too long): {self._isolation_line_length}")

        # Find and store the midpoint of the scribe path.
        self._midpoint: Point = Point((self._cell_parameters.origin.x * 2
                                       + self._cell_parameters.default_pass_gap
                                       + self._p1_specific.isolation_line_spacing) / 2
                                      , (self._cell_parameters.origin.y
                                         * 2 + self._isolation_line_length) / 2)

        # if self._debug_mode:
        #     self._logger.debug(f"Calculated midpoint: x={self._midpoint.x}, y={self._midpoint.y}")

    #endregion

    #region Basic Movements
    def _initial_move(
            self,
            line_type: _LINE_TYPES = "isolation"
    ) -> PathNode:
        """
        Adds the initial movement towards the origin position to the path.
        
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: PathNode.
        :return: The initial move location.
        """

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Initial move to origin: "
        #         f"x={self._cell_parameters.origin.x}, y={self._cell_parameters.origin.y}, type={line_type}"
        #     )

        return PathNode(
            pos=self._cell_parameters.origin,
            beam_state=False,
            approach_speed=self._laser_data.translation_speed,
            line_type=line_type
        )

    def _make_alternating_nodes(
            self,
            points: list[Point],
            translation_speed: float,
            scribe_speed: float,
            line_type: _LINE_TYPES = "cell",
            beam_state: bool = True
    ) -> list[PathNode]:
        """
        Converts a list of point to PathNodes with alternating beam state, on and off, true and false. 
        Then return the sub path.
        
        :param points: list[Point]: The points to turn into PathNodes.
        :param translation_speed: float: The speed of the laser translation.
        :param scribe_speed: float: The speed of the laser scribing.
        :param line_type: _LINE_TYPES: The type of line.
        :param beam_state: bool: The state of the beam on approach to the sub path from the previous position in the 
            global path.
        :rtype: list[PathNode].
        :return: The generated sub path of alternating PathNodes.
        """
        # Makes sure the literal passed into the function is valid, throws error otherwise.

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Making alternating nodes, type={line_type}, count={len(points)}, init_beam_state={beam_state}"
        #     )

        # Sub path to build the PathNode list.
        sub_path: list[PathNode] = []
        
        # Creates the list of PathNodes with alternating beam state, and corresponding travel speed.
        for i, pos in enumerate(points):
            sub_path.append(PathNode(
                pos=pos,
                beam_state=beam_state,
                approach_speed=(scribe_speed if beam_state else translation_speed),
                line_type=line_type
            ))
            
            # if self._debug_mode:
            #     self._logger.debug(
            #         f"  Node {i}: x={pos.x:.2f}, y={pos.y:.2f}, beam={beam_state}"
            #         f", speed={scribe_speed if beam_state else translation_speed}"
            #     )
            
            beam_state = not beam_state
        # end for

        return sub_path

    def _point_path(
            self,
            start_pos: Point,
            length: float,
            width: float,
            start_orientation: _START_POSITIONS
    ) -> list[Point]:
        """
        Makes a zigzag pattern of points in the form of a path.

        :param start_pos: The starting position of the path.
        :param length: The length of the path.
        :param width: The width of the path.
        :param start_orientation: The starting orientation of the path.
        :rtype: list[Point].
        :return: The path of points.
        """
        # Makes sure the literal passed into the function is valid, throws error otherwise.

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Creating point path: "
        #         f"start="
        #         f"({start_pos.x:.2f},{start_pos.y:.2f}), length={length}, width={width}, orientation={start_orientation}"
        #     )

        # Sets the direction the path is generated in from the starting orientation.
        x_direction, y_direction = _START_DIRECTIONS[start_orientation]["x_direction"], \
        _START_DIRECTIONS[start_orientation]["y_direction"]

        # if self._debug_mode:
        #     self._logger.debug(f"  Direction factors: x_direction={x_direction}, y_direction={y_direction}")

        # Translates the start position to the bottom of the scribe path if it starts in the middle.
        match start_orientation:
            case "middle_left":
                start_pos = start_pos.translate(dy=-width / 2)
                if self._debug_mode:
                    self._logger.debug(f"  Adjusted start for middle_left: ({start_pos.x:.2f},{start_pos.y:.2f})")
            case "middle_right":
                start_pos = start_pos.translate(dy=-width / 2)
                if self._debug_mode:
                    self._logger.debug(f"  Adjusted start for middle_right: ({start_pos.x:.2f},{start_pos.y:.2f})")

        # Generates the points of the path from translations, rounding to 5 decimal places.
        first_pos: Point = round(start_pos.translate(dx=length * x_direction), 5)
        second_pos: Point = round(first_pos.translate(dy=width * y_direction), 5)
        third_pos: Point = round(second_pos.translate(dx=-length * x_direction), 5)
        fourth_pos: Point = round(third_pos.translate(dy=width * y_direction), 5)

        # Makes the path from the translated points.
        point_path: list[Point] = [
            first_pos,
            second_pos,
            third_pos,
            fourth_pos
        ]

        # Shows the points in the debug output.
        # if self._debug_mode:
        #     self._logger.debug("  Generated points:")
        # for index, point in enumerate(point_path):
        #     if self._debug_mode:
        #         self._logger.debug(f"    Point {index}: ({point.x:.2f},{point.y:.2f})")

        return point_path

    def _path_node_maker(
            self,
            pass_count: int,
            start_pos: Point,
            length: float,
            width: float,
            start_orientation: _START_POSITIONS,
            translation_speed: float,
            scribing_speed: float,
            line_type: _LINE_TYPES,
            beam_state: bool = False
    ) -> list[PathNode]:
        """
        Makes a zigzag pattern of PathNodes using the _point_path method as a base. 
        Creates a zigzag pattern of points, then converts them to nodes with alternating beam state using 
        _make_alternating_nodes.

        :param pass_count: The number of passes.
        :param start_pos: The starting position of the path.
        :param length: The length of the path to make for the cell.
        :param width: The width of the path to make for the cell.
        :param start_orientation: The starting orientation.
        :param translation_speed: The speed when translating the laser.
        :param scribing_speed: The speed when scribing with the laser.
        :param line_type: The type of the line for viewing the path.
        :param beam_state: The state of the beam on approach to the first path node in the sub path.
        :rtype: list[PathNode].
        :return: The generated path of alternating PathNodes.
        """
        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Making path nodes: type={line_type}, pass_count={pass_count}, start=({start_pos.x:.2f},{start_pos.y:.2f})"
        #     )
        #     self._logger.debug(
        #         f"  Parameters: length={length}, width={width}, orientation={start_orientation}"
        #     )

        sub_path: list[PathNode] = []

        for i in range(pass_count):
            # if self._debug_mode:
            #     self._logger.debug(f"  Creating pass {i + 1}/{pass_count}")

            current_start = sub_path[-1].pos if sub_path else start_pos

            # if self._debug_mode:
            #     self._logger.debug(
            #         f"    Pass start: ({current_start.x:.2f},{current_start.y:.2f})"
            #     )

            # Build the zigzag point path.
            point_path = self._point_path(
                start_pos=current_start,
                length=length,
                width=width,
                start_orientation=start_orientation
            )

            # Every pass is a full four-point zigzag: scribe, step, scribe, step. The previous pass already ends
            # with a beam OFF step that leaves the laser at this pass's start, so later passes simply begin with
            # the beam ON. (The old code inserted a travel node to point_path[0] and then started the remaining
            # three points ON, which flipped the parity: the long lines were travelled and the 0.05 steps were
            # scribed on every pass after the first.)
            nodes = self._make_alternating_nodes(
                points=point_path,
                translation_speed=translation_speed,
                scribe_speed=scribing_speed,
                line_type=line_type,
                beam_state=beam_state if i == 0 else True
            )
            sub_path.extend(nodes)

            # if self._debug_mode:
            #     self._logger.debug(f"    Sub_path now has {len(sub_path)} nodes")

        # if self._debug_mode:
        #     self._logger.debug(f"  Completed path_node_maker with {len(sub_path)} nodes")
        
        return sub_path

    #endregion

    #region Isolation Lines
    def _single_isolation_line(
            self,
            start_pos: Point,
            line_type: _LINE_TYPES = "isolation"
    ) -> list[PathNode]:
        """
        Returns the path nodes for one isolation line.
        
        :param start_pos: The starting position of the isolation line.
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: list[PathNode].
        :return: The path for a single isolation line.
        """
        # Makes sure the literal passed into the function is valid, throws error otherwise.

        # if self._debug_mode:
        #     self._logger.debug(f"Creating single isolation line: start=({start_pos.x:.2f},{start_pos.y:.2f})")

        # Sub path to build the isolation line.
        sub_path: list[PathNode] = []

        # Each vertex of the isolation line path.
        first_pos: Point = start_pos.translate(dy=self._isolation_line_length)
        second_pos: Point = first_pos.translate(dx=self._p2_specific.pass_gap)
        third_pos: Point = second_pos.translate(dy=-self._isolation_line_length)

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"  Isolation points: "
        #         f"({start_pos.x:.2f},{start_pos.y:.2f}) "
        #         f"-> ({first_pos.x:.2f},{first_pos.y:.2f}) "
        #         f"-> ({second_pos.x:.2f},{second_pos.y:.2f}) "
        #         f"-> ({third_pos.x:.2f},{third_pos.y:.2f})"
        #     )

        # Make an alternating path from the vertices and append it to sub_path.
        sub_path.extend(
            self._make_alternating_nodes(
                points=[first_pos, second_pos, third_pos],
                translation_speed=self._laser_data.translation_speed,
                scribe_speed=self._laser_data.scribing_speed,
                line_type=line_type,
                beam_state=True
            )
        )

        # if self._debug_mode:
        #     self._logger.debug(f"  Created isolation line with {len(sub_path)} nodes")
        
        return sub_path

    def _both_isolation_lines(
            self,
            start_pos: Point,
            line_type: _LINE_TYPES = "isolation"
    ) -> list[PathNode]:
        """
        Returns the path nodes for both isolation lines and the transition between them.

        :param start_pos: The starting position of the isolation line.
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: list[PathNode].
        :return: The path for two isolation lines and the transition between them.
        """
        # Makes sure the literal passed into the function is valid, throws error otherwise.

        # if self._debug_mode:
        #     self._logger.debug(f"Creating both isolation lines: start=({start_pos.x:.2f},{start_pos.y:.2f})")

        # Sub path to build the isolation lines.
        sub_path: list[PathNode] = []

        # Add an isolation line starting at the current path position.
        first_line = self._single_isolation_line(start_pos, line_type)
        sub_path.extend(first_line)
        
        # if self._debug_mode:
        #     self._logger.debug(f"  Added first isolation line with {len(first_line)} nodes")

        # Translate across the panel to the other isolation line.
        transition_pos = sub_path[-1].pos.translate(dx=self._p1_specific.isolation_line_spacing)
        
        # if self._debug_mode:
        #     self._logger.debug(
        #         f"  Transition to second isolation line: ({transition_pos.x:.2f},{transition_pos.y:.2f})"
        #     )

        # Still translating.
        sub_path.append(PathNode(
            pos=transition_pos,
            beam_state=False,
            approach_speed=self._laser_data.translation_speed,
            line_type=line_type
        ))

        # Add an isolation line starting at the current sub path position.
        second_line = self._single_isolation_line(sub_path[-1].pos, line_type)
        sub_path.extend(second_line)
        
        # if self._debug_mode:
        #     self._logger.debug(f"  Added second isolation line with {len(second_line)} nodes")
        #     self._logger.debug(f"  Total isolation nodes: {len(sub_path)}")

        return sub_path

    def _isolation_cell_transition(
            self,
            start_pos: Point,
            line_type: _LINE_TYPES = "isolation"
    ) -> list[PathNode]:
        """
        Returns the path between the end of the isolation lines, and the start of the cells.

        :param start_pos: The starting position of the isolation line.
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: list[PathNode].
        :return: The transition path between scribing the isolation lines and the cells.
        """
        # if self._debug_mode:
        #     self._logger.debug(f"Creating isolation to cell transition: start=({start_pos.x:.2f},{start_pos.y:.2f})")

        # Sub path to build the cell transition line.
        sub_path: list[PathNode] = []

        # FIX: Replaced the erroneous cell_length / 2 calculation with a proper 
        # horizontal offset that matches your cell grid spacing (using default pass gap 
        # or isolation spacing rather than scaling the cell length dimension).
        cell_isolation_offset: float = self._cell_parameters.default_pass_gap

        # if self._debug_mode:
        #     self._logger.debug(f"  Calculated cell_isolation_offset: {cell_isolation_offset}")

        # Each vertex of the isolation to cell transition path.
        first_pos: Point = start_pos.translate(dy=((self._isolation_line_length
                                                    - (self._cell_parameters.cell_width
                                                       * self._cell_parameters.cell_count))
                                                   / 2))
        second_pos: Point = first_pos.translate(dx=cell_isolation_offset)

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"  Transition points: ({first_pos.x:.2f},{first_pos.y:.2f}) -> ({second_pos.x:.2f},{second_pos.y:.2f})"
        #     )

        # Append the second vertex as a path node with the appropriate beam state.
        sub_path.append(PathNode(
            pos=second_pos,
            beam_state=False,
            approach_speed=self._laser_data.translation_speed,
            line_type=line_type
        ))

        # if self._debug_mode:
        #     self._logger.debug(f"  Created transition with {len(sub_path)} nodes")
        
        return sub_path

    #endregion

    #region Cells
    
    #region P1 Cells
    def _single_four_line_cell(
            self,
            start_pos: Point,
            do_p1: bool,
            cell_width: float,
            cell_length: float,
            number_of_passes: int,
            pass_gap: float,
            start_orientation: _START_POSITIONS,
            line_type: _LINE_TYPES = "cell"
    ) -> list[PathNode]:
        """
        Returns the path nodes for one cell scribe.
        
        :param start_pos: The starting position of the cell.
        :param do_p1: The condition on which p1 or p2 is generated.
        :param cell_width: The width of the cells being generated.
        :param cell_length: The length of the cells being generated.
        :param number_of_passes: The number of passes to do for a cell edge.
        :param pass_gap: The gap between passes on a cell edge.
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: list[PathNode].
        :return: The path nodes defining a single cell.
        """
        # Makes sure the literal passed into the function is valid, throws error otherwise.

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Creating single cell: start=({start_pos.x:.2f},{start_pos.y:.2f}), is_p1={self._laser_data.is_p1}"
        #     )

        # Determine pass count and width based on P1 or P2.
        actual_pass_count = 1 if do_p1 else number_of_passes
        actual_width = cell_width if do_p1 else pass_gap
        # actual_pass_gap = 0 if do_p1 else cell_width

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"  Cell parameters: pass_count={actual_pass_count}, width={actual_width}, pass_gap={actual_pass_gap}"
        #     )

        # Sub path to build the cell line, zigzag of alternating PathNodes.
        sub_path: list[PathNode] = self._path_node_maker(
            pass_count=actual_pass_count,
            start_pos=start_pos,
            length=cell_length,
            width=actual_width,
            start_orientation=start_orientation,
            translation_speed=self._laser_data.translation_speed,
            scribing_speed=self._laser_data.scribing_speed,
            line_type=line_type,
            beam_state=True
        )

        # if self._debug_mode:
        #     self._logger.debug(f"  Created single cell with {len(sub_path)} nodes")
        
        return sub_path
    
    #endregion
    
    #region P2 Cells
    def _single_p2_cell(
            self,
            start_pos: Point,
            start_orientation: _START_POSITIONS,
            line_type: _LINE_TYPES = "cell"
    ) -> list[PathNode]:
        """
        Generates a p2 cell with multiple passes using pass_gap.
        
        :param start_pos: The starting position of the p2 scribe.
        :param start_orientation: The starting orientation of the p2 scribe.
        :param line_type: The type of line.
        :rtype: list[PathNode]
        :return: 
        """
        sub_path: list[PathNode] = []
        
        # % P2 cell edge generation using the actual multi-pass parameters
        cell_nodes = self._single_four_line_cell(
            start_pos=start_pos,
            do_p1=False,
            cell_width=self._p2_specific.pass_gap,
            cell_length=self._cell_parameters.cell_length,
            number_of_passes=self._p2_specific.pass_count,
            pass_gap=self._p2_specific.pass_gap,
            start_orientation=start_orientation,
            line_type=line_type
        )
        sub_path.extend(cell_nodes)
        
        return sub_path
    
    #endregion

    #region General Cells
    def _all_cells(
            self,
            start_pos: Point,
            do_p1: bool,
            cell_width: float,
            number_of_cells: int,
            start_orientation: _START_POSITIONS,
            line_type: _LINE_TYPES = "cell"
    ) -> list[PathNode]:
        """
        Returns the path for all the cells on the panel.
        
        :param start_pos: The starting position of the cells.
        :param do_p1: The condition on which p1 or p2 is generated.
        :param cell_width: The width of the cells that are generated.
        :param number_of_cells: The number of cells to generate.
        :param start_orientation: The starting orientation of the cell path.
        :param line_type: _LINE_TYPES: The type of line.
        :rtype: list[PathNode].
        :return: The constructed cell paths.
        """
        sub_path: list[PathNode] = []

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Creating all cells: start=({start_pos.x:.2f},{start_pos.y:.2f})"
        #         f", cell_count={number_of_cells}"
        #     )

        # For P1, each cell iteration handles 2 lines/passes. 
        # Using floor division prevents rounding up and creating an extra overlapping loop.
        actual_cell_count = number_of_cells // 2 if do_p1 else number_of_cells
        remainder_cell = number_of_cells % 2 if do_p1 else 0

        # Generate all the p1 cells.
        if do_p1:
            for i in range(actual_cell_count):
                # if self._debug_mode:
                #     self._logger.debug(f"  Creating cell pass {i + 1}/{actual_cell_count}")

                # Get start position for this cell.
                cell_start = sub_path[-1].pos if sub_path else start_pos

                # if self._debug_mode:
                #     self._logger.debug(f"    Cell start: ({cell_start.x:.2f},{cell_start.y:.2f})")

                # Append the cell to the path.
                cell_nodes = self._single_four_line_cell(
                    start_pos=cell_start, 
                    do_p1=do_p1,
                    cell_width=cell_width,
                    cell_length=self._cell_parameters.cell_length,
                    number_of_passes=self._p2_specific.pass_count,
                    pass_gap=self._p2_specific.pass_gap,
                    start_orientation=start_orientation,
                    line_type=line_type
                )
                sub_path.extend(cell_nodes)

                # if self._debug_mode:
                #     self._logger.debug(f"    Added cell with {len(cell_nodes)} nodes, sub_path now has {len(sub_path)} nodes")

            # Handle any odd remainder cell cleanly with a single straight line instead of a full box loop
            if remainder_cell > 0:
                if self._debug_mode:
                    self._logger.debug("  Creating final remainder cell pass for odd count")
                
                cell_start = sub_path[-1].pos if sub_path else start_pos
                x_direction = _START_DIRECTIONS[start_orientation]["x_direction"]
                final_node_point = cell_start.translate(dx=self._cell_parameters.cell_length * x_direction)
                
                sub_path.append(PathNode(
                    pos=round(final_node_point, 5),
                    beam_state=True,
                    approach_speed=self._laser_data.scribing_speed,
                    line_type=line_type
                ))

            # if self._debug_mode:
            #     self._logger.debug(f"  Created all P1 cells with final count of {len(sub_path)} nodes")

        else:
            # Each P2 cell zigzag ends at the same x it started at (see _point_path), so the orientation must
            # stay constant. Flipping it would mirror every other cell horizontally.
            for i in range(number_of_cells):
                # Step from each cell's own origin so the pitch is exactly cell_width. Stepping from the previous
                # cell's last node adds that cell's own height (pass_count * 2 * pass_gap) to every pitch.
                cell_origin = round(start_pos.translate(dy=cell_width * i), 5)

                if i > 0:
                    # Travel to the next cell with the beam OFF. Cell 0 is reached by the caller's travel node.
                    sub_path.append(PathNode(
                        pos=cell_origin,
                        beam_state=False,
                        approach_speed=self._laser_data.translation_speed,
                        line_type=line_type
                    ))

                # if self._debug_mode:
                #     self._logger.debug(
                #         f"  Creating P2 cell {i + 1}/{number_of_cells} at "
                #         f"({cell_origin.x:.2f},{cell_origin.y:.2f}), orientation={start_orientation}"
                #     )

                cell_nodes = self._single_p2_cell(
                    start_pos=cell_origin,
                    start_orientation=start_orientation,
                    line_type=line_type
                )
                sub_path.extend(cell_nodes)

        return sub_path

    #endregion

    #region Bus Bars
    def _single_bus_bar(
            self,
            start_pos: Point,
            start_orientation: _START_POSITIONS,
            line_type: _LINE_TYPES = "bus_bar"
    ) -> list[PathNode]:
        """
        Returns the path for a single bus bar.

        :param start_pos: The starting position of the bus bar.
        :param start_orientation: The starting orientation of the bus bar.
        :param line_type: The type of the line for viewing the path.
        :rtype: list[PathNode].
        :return: The constructed bus bar path.
        """

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Creating single bus bar: start=({start_pos.x:.2f},{start_pos.y:.2f}), orientation={start_orientation}"
        #     )

        # Calculate total desired passes based on bus bar width and pass gap.
        if self._p2_specific.pass_gap:
            raw_pass_count = round(self._p2_specific.bus_bar_width / self._p2_specific.pass_gap)
        else:
            raw_pass_count = round(self._p2_specific.bus_bar_width / self._cell_parameters.default_pass_gap)
        
        # Each iteration of _path_node_maker generates 2 lines (a pair). 
        # Using floor division prevents doubling the pass count and overlapping.
        pass_pairs = max(1, raw_pass_count // 2)
        remainder_pass = raw_pass_count % 2

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"  Bus bar parameters: width={self._p2_specific.bus_bar_width}, pass_gap={self._p2_specific.pass_gap}"
        #         f", calculated pass_pairs={pass_pairs}, remainder={remainder_pass}"
        #     )

        # Sub path to build the line for the bus bar pairs.
        sub_path: list[PathNode] = self._path_node_maker(
            pass_count=pass_pairs,
            start_pos=start_pos,
            length=self._cell_parameters.cell_length,
            width=self._p2_specific.pass_gap,
            start_orientation=start_orientation,
            translation_speed=self._p2_specific.bus_bar_speed,
            scribing_speed=self._laser_data.scribing_speed,
            line_type=line_type,
            beam_state=True
        )

        # Handle any odd remainder pass cleanly with a single straight line
        if remainder_pass > 0:
            current_start = sub_path[-1].pos if sub_path else start_pos
            x_direction = _START_DIRECTIONS[start_orientation]["x_direction"]
            final_node_point = current_start.translate(dx=self._cell_parameters.cell_length * x_direction)
            
            sub_path.append(PathNode(
                pos=round(final_node_point, 5),
                beam_state=True,
                approach_speed=self._laser_data.scribing_speed,
                line_type=line_type
            ))

        # if self._debug_mode:
        #     self._logger.debug(f"  Created bus bar with {len(sub_path)} nodes")
        return sub_path

    #endregion

    #region Path Rotation
    def _rotate_path(
            self,
            path: list[PathNode],
            rotation_angle: np.float64,
            rotation_point: Point | None = None,
            angle_units: _ANGLE_UNITS = "degrees"
    ) -> list[PathNode]:
        """
        Rotates the laser scribing path.

        :param path: The path to rotate.
        :param rotation_angle: The angle at which to rotate the path, in degrees or radians.
        :param rotation_point: The point about which to rotate the path.
        :param angle_units: The unit type of the angle.
        :rtype: list[PathNode].
        :return: The path rotated by the given rotation in degrees.
        """

        if rotation_point is None:
            rotation_point = Point(x=150, y=150)

        # if self._debug_mode:
        #     self._logger.debug(
        #         f"Rotating path: "
        #         f"angle={rotation_angle}, point=({rotation_point.x:.2f},{rotation_point.y:.2f}), units={angle_units}"
        #     )

        # Converts the angle to radian for further calculation.
        match angle_units:
            case "degrees":
                # Convert the rotation angle to radians.
                θ: np.float64 = rotation_angle * np.float64(np.pi / 180)
                # if self._debug_mode:
                #     self._logger.debug(f"  Converting {rotation_angle} degrees to {θ:.6f} radians")
            case "radians":
                # Keeps the rotation angle as radians.
                θ: np.float64 = rotation_angle
                # if self._debug_mode:
                #     self._logger.debug(f"  Using angle directly as radians: {θ:.6f}")
            case _:
                # Keeps the rotation angle the same as entered.
                θ: np.float64 = rotation_angle
                # if self._debug_mode:
                #     self._logger.debug(f"  Using angle directly (default): {θ:.6f}")

        # Define the rotation matrix.
        rotation_matrix = np.array([[np.cos(θ), -np.sin(θ)],
                                    [np.sin(θ), np.cos(θ) ]])
        # Simplify the rotation point.
        h: float = rotation_point.x
        k: float = rotation_point.y

        # if self._debug_mode:
        #     self._logger.debug(f"  Rotating {len(path)} points around ({h:.2f},{k:.2f})")

        # Rotate every node on the path around the rotation point.
        for i in range(len(path)):
            # Get the coordinates from the original point.
            x: float = path[i].pos.x
            y: float = path[i].pos.y

            # Get the point to translate the rotated point by.
            translation_point = np.array([[x - h],
                                           [y - k]])
            
            # Get the rotated point by multiplying by the rotation matrix.
            rotated_point = rotation_matrix @ translation_point
            # Translate the rotated point.
            rotated_point = rotated_point[0][0] + h, rotated_point[1][0] + k

            # Set the new rotated point.
            path[i].pos.x = rotated_point[0]
            path[i].pos.y = rotated_point[1]

            # if i % 10 == 0 and self._debug_mode:  # Log only some points to avoid excessive output
            #     self._logger.debug(
            #         f"    Rotated point {i}: ({x:.2f},{y:.2f}) -> ({path[i].pos.x:.2f},{path[i].pos.y:.2f})"
            #     )
        # end for

        # if self._debug_mode:
        #     self._logger.debug("  Rotation complete")
            
        return path

    #endregion

    #region Path Generator
    def generate_path(
            self
    ) -> list[PathNode] | None:
        """
        Generates the path a laser scriber will follow to make a solar panel as a series of vertices. 
        Stored as PathNodes in a list.

        :rtype: list[PathNode].
        :return: The path a laser scriber will follow as a series of vertices.
        """
        # if self._debug_mode:
        #     self._logger.debug("=== Generating Path ===")

        # // Adds the origin to the path.
        self._path.append(self._initial_move(line_type="isolation"))
        
        # if self._debug_mode:
        #     self._logger.debug(f"Added initial move to origin: ({self._path[0].pos.x:.2f},{self._path[0].pos.y:.2f})")

        # * Add isolation lines to the path.
        isolation_lines = self._both_isolation_lines(start_pos=self._path[-1].pos, line_type="isolation")
        self._path.extend(isolation_lines)
        
        # if self._debug_mode:
        #     self._logger.debug(f"Added isolation lines with {len(isolation_lines)} nodes")

        # * Adds the transition line between the cells and the isolation lines.
        transition = self._isolation_cell_transition(start_pos=self._path[-1].pos, line_type="isolation")
        self._path.extend(transition)
        
        # if self._debug_mode:
        #     self._logger.debug(f"Added isolation-cell transition with {len(transition)} nodes")

        # // Gets the cell starting point.
        bus_and_cell_start: Point = self._path[-1].pos
        
        # if self._debug_mode:
        #     self._logger.debug(f"Bus and cell start position: ({bus_and_cell_start.x:.2f},{bus_and_cell_start.y:.2f})")

        # @ Only executed on p2 scribes.
        if not self._laser_data.is_p1:
            
            # if self._debug_mode:
            #     self._logger.debug("P2 mode - clearing path and starting with bus bars")
            
            # For debugging.
            # path_before_clear = len(self._path)
            
            # // Clears the isolation lines from the path since they're only useful for orienting the scribe in p2.
            self._path.clear()
            
            # if self._debug_mode:
            #     self._logger.warning(f"ATTENTION: Cleared {path_before_clear} nodes from path in P2 mode!")

            # ! First bus bar.
            first_bus_pos = bus_and_cell_start.translate(dy=-self._p2_specific.p2_bus_spacing)
            
            # if self._debug_mode:
            #     self._logger.debug(f"First bus bar position: ({first_bus_pos.x:.2f},{first_bus_pos.y:.2f})")

            # The path was just cleared, so travel to the first bus bar with the beam OFF before scribing.
            self._path.append(PathNode(
                pos=first_bus_pos,
                beam_state=False,
                approach_speed=self._laser_data.translation_speed,
                line_type="bus_bar"
            ))

            # ! Also first bus bar.
            first_bus = self._single_bus_bar(
                start_pos=first_bus_pos,
                line_type="bus_bar",
                start_orientation="top_right"
            )
            # Remove extraneous trailing beam off node (only if it is one).
            if first_bus and not first_bus[-1].beam_state:
                first_bus.pop()
            self._path.extend(first_bus)
            
            # if self._debug_mode:
            #     self._logger.debug(f"Added first bus bar with {len(first_bus)} nodes")

        # % Add the cells to the path.
        cells: list[PathNode] = []

        # @ Add p1 cells.
        if self._laser_data.is_p1:
            cells = self._all_cells(start_pos=bus_and_cell_start, 
                                    do_p1=self._laser_data.is_p1, 
                                    cell_width=self._cell_parameters.cell_width, 
                                    number_of_cells=self._cell_parameters.cell_count, 
                                    start_orientation="bottom_right", 
                                    line_type="cell"
                                    )
            self._path.extend(cells)
        elif not self._laser_data.is_p1:
            cell_start_pos = bus_and_cell_start.translate(dy=self._p2_specific.initial_offset)
            
            # Insert a safe travel move (beam OFF) from the first bus bar to the cells
            self._path.append(PathNode(
                pos=cell_start_pos,
                beam_state=False,
                approach_speed=self._laser_data.translation_speed,
                line_type="cell"
            ))

            cells = self._all_cells(start_pos=cell_start_pos, 
                                    cell_width=self._cell_parameters.cell_width, 
                                    do_p1=self._laser_data.is_p1, 
                                    number_of_cells=self._cell_parameters.cell_count, 
                                    start_orientation="bottom_right", 
                                    line_type="cell"
                                    )
            # Remove extraneous trailing beam off node (only if it is one).
            if cells and not cells[-1].beam_state:
                cells.pop()
            self._path.extend(cells)
        
        # if self._debug_mode:
        #     self._logger.debug(f"Added cells with {len(cells)} nodes")

        # @ Only executed on p2 scribes.
        if not self._laser_data.is_p1:
            # ! Second bus bar.
            # The second bus bar sits just past the far edge of the last cell, mirroring the first bus bar which sits
            # just before the first cell. bus_bar_spacing is the clearance between the cell array and this bus bar.
            cell_array_length: float = self._cell_parameters.cell_count * self._cell_parameters.cell_width
            second_bus_pos = bus_and_cell_start.translate(
                dy=self._p2_specific.initial_offset + cell_array_length + self._p2_specific.bus_bar_spacing
            )
            
            # if self._debug_mode:
            #     self._logger.debug(f"Second bus bar position: ({second_bus_pos.x:.2f},{second_bus_pos.y:.2f})")

            # Insert a safe travel move (beam OFF) from the cells to the second bus bar
            self._path.append(PathNode(
                pos=second_bus_pos,
                beam_state=False,
                approach_speed=self._laser_data.translation_speed,
                line_type="bus_bar"
            ))

            # ! Also second bus bar.
            second_bus = self._single_bus_bar(
                start_pos=second_bus_pos,
                line_type="bus_bar",
                start_orientation="bottom_right"
            )
            # Remove extraneous trailing beam off node (only if it is one).
            if second_bus and not second_bus[-1].beam_state:
                second_bus.pop()
            self._path.extend(second_bus)
            
            # if self._debug_mode:
            #     self._logger.debug(f"Added second bus bar with {len(second_bus)} nodes")

        # if self._debug_mode:
        #     self._logger.debug(f"Path before rotation has {len(self._path)} nodes")

        # @ Rotates the path by the rotation amount if the rotation is not 0.
        if self._rotation:
            # if self._debug_mode:
            #     self._logger.debug(f"Rotating path by {self._rotation} degrees")
            
            # The point about which to rotate the scribe, generally the middle of the scribe or the panel.
            rotation_point = bus_and_cell_start
            
            # if self._debug_mode:
            #     self._logger.debug(f"Rotation point: ({rotation_point.x:.2f},{rotation_point.y:.2f})")

            # Perform the rotation on the path.
            self._path = self._rotate_path(
                path=self._path,
                rotation_angle=self._rotation,
                rotation_point=rotation_point,
                angle_units="degrees"
            )
        # else: # Logs that no rotation was applied.
        #     if self._debug_mode:
        #         self._logger.debug("No rotation applied (rotation = 0)")

        # Log summary of the final path.
        # if self._debug_mode:
        #     self._logger.debug(f"Final path has {len(self._path)} nodes")

        # Log first 5 and last 5 nodes of the path
        # if len(self._path) > 0:
            # if self._debug_mode:
            #     self._logger.debug("First 5 nodes of path:")
            # for i in range(min(5, len(self._path))):
            #     node = self._path[i]
                # if self._debug_mode:
                #     self._logger.debug(
                #         f"  Node {i}: ({node.pos.x:.2f},{node.pos.y:.2f}), beam={node.beam_state}, type={node.line_type}")

            # if self._debug_mode:
            #     self._logger.debug("Last 5 nodes of path:")
            # for i in range(max(0, len(self._path) - 5), len(self._path)):
            #     node = self._path[i]
                # if self._debug_mode:
                #     self._logger.debug(
                #         f"  Node {i}: ({node.pos.x:.2f},{node.pos.y:.2f}), beam={node.beam_state}, type={node.line_type}")

        # Log extreme coordinate values
        # if len(self._path) > 0:
        #     x_coords = [node.pos.x for node in self._path]
        #     y_coords = [node.pos.y for node in self._path]
            # if self._debug_mode:
            #     self._logger.debug(f"X range: {min(x_coords):.2f} to {max(x_coords):.2f}")
            #     self._logger.debug(f"Y range: {min(y_coords):.2f} to {max(y_coords):.2f}")

        # Return the constructed path.
        return self._path

    #endregion