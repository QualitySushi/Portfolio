from __future__ import annotations

from typing import Literal

from core.generator import Generator
from core.path_node import PathNode

_LINE_COLORS = Literal["blue", "green", "red", "black"]
_LINE_TYPES = Literal["isolation", "cell", "bus_bar"]


class SvgGenerator(Generator):
    """
    Generator for producing SVG command output from path nodes.
    """

    def _initialize(self) -> None:
        """
        Initialize SVG-specific settings for generator object.
        
        :rtype: None
        """
        self._commands: list[str] = []
        self._current_x: float | None = None
        self._current_y: float | None = None
        self._last_set_speed: float | None = None
        self._current_beam_state: bool | None = False

    def generate(self) -> str:
        """
        Generate SVG format commands from path nodes
        
        :return: Returns the completed SVG as a string. 
        :rtype: str
        """
        self.cleanup()
        
        # Gets dimensions for the SVG header.
        width, height, min_x, min_y, _max_x, _max_y = self._get_path_bounds(self._path_nodes)
        
        # SVG Header with viewBox to ensure proper sizing and positioning
        self._commands.append(f'<svg '
                            f'width="{width}" '
                            f'height="{height}" '
                            f'viewBox="{min_x} {min_y} {width} {height}" '
                            f'xmlns="http://www.w3.org/2000/svg">')
        
        match self._path_nodes[0].line_type:
            case "bus_bar":
                self._commands.append("\n  <!-- Bus Bar 1 -->")
            case "isolation":
                self._commands.append("\n  <!-- Isolation Layer -->")
            case _:
                pass
        
        for node in range(len(self._path_nodes) - 1):
            # Gets the start and end position of the line.
            start_node = self._path_nodes[node]
            end_node = self._path_nodes[node + 1]
            
            match start_node.beam_state:
                case True:
                    continue
                case False:
                    pass
            
            # Adds a comment header for isolation, bus bar, and cell sections of the SVG.
            match start_node.line_type:
                case "isolation":
                    match end_node.line_type:
                        case "cell":
                            self._commands.append("\n  <!-- Cell Layer -->")
                        case _:
                            pass
                case "bus_bar":
                    match end_node.line_type:
                        case "cell":
                            self._commands.append("\n  <!-- Cell Layer -->")
                        case _:
                            pass
                case "cell":
                    match end_node.line_type:
                        case "bus_bar":
                            self._commands.append("\n  <!-- Bus Bar 2 -->")
                        case _:
                            pass

            # Update position if changed.
            if start_node.pos.x != self._current_x or start_node.pos.y != self._current_y:
                self._add_move(start_node, end_node)
        
        # SVG footer.
        self._commands.append("\n</svg>")

        return "\n".join(self._commands)

    def _add_move(self, start_node: PathNode, end_node: PathNode) -> None:
        """
        Generate a line between the start and the end node in SVG format and return.
        
        :param start_node: The start position of the line.
        :param end_node: The end position of the line.
        :rtype: None
        """
        # Create an SVG line.
        if start_node.pos.x != self._current_x or start_node.pos.y != self._current_y:
            self._commands.append(f"  <line "
                                  f"x1=\"{start_node.pos.x:.4f}\" "
                                  f"y1=\"{start_node.pos.y:.4f}\" "
                                  f"x2=\"{end_node.pos.x:.4f}\" "
                                  f"y2=\"{end_node.pos.y:.4f}\" "
                                  f"stroke=\"{self._get_color(end_node)}\" "
                                  f"stroke-width=\"1\""
                                  f"/>")
            self._current_x = start_node.pos.x
            self._current_y = start_node.pos.y
    
    def _get_color(self, node: PathNode) -> _LINE_COLORS:
        """
        Determines what color a line should be based on the second point and returns.

        :param node: The second point of a line to get the line color of.
        :return: Returns the line color for the current line.
        :rtype: _LINE_COLORS
        """
        match node.line_type:
            case "cell":
                return "blue"
            case "isolation":
                return "green"
            case "bus_bar":
                return "red"
            case _:
                return "black"
        
    def _get_path_bounds(self, path: list[PathNode]) -> tuple[int, int, int, int, int, int]:
        """
        Finds the dimensions and bounds of the given path and returns.

        :param path: The path of PathNodes to find the bounds of. 
        :return: A tuple containing (width, height, min_x, min_y, max_x, max_y)
        :rtype: tuple[int, int, int, int, int, int]
        """
        if not path:
            return 100, 100, 0, 0, 100, 100  # Default size if no path
        
        boundary_coordinates = {
            "max_x": path[0].pos.x,
            "min_x": path[0].pos.x,
            "max_y": path[0].pos.y,
            "min_y": path[0].pos.y
        }
        
        # Gets the maximum and minimum values in the path.
        for node in path:
            current_x = node.pos.x
            current_y = node.pos.y
            
            boundary_coordinates["max_x"] = max(boundary_coordinates["max_x"], current_x)
            boundary_coordinates["min_x"] = min(boundary_coordinates["min_x"], current_x)
            boundary_coordinates["max_y"] = max(boundary_coordinates["max_y"], current_y)
            boundary_coordinates["min_y"] = min(boundary_coordinates["min_y"], current_y)
        
        # Add padding
        padding = 10
        min_x = boundary_coordinates["min_x"] - padding
        min_y = boundary_coordinates["min_y"] - padding
        max_x = boundary_coordinates["max_x"] + padding
        max_y = boundary_coordinates["max_y"] + padding
        
        # Calculate width and height
        width = max_x - min_x
        height = max_y - min_y
        
        return int(width), int(height), int(min_x), int(min_y), int(max_x), int(max_y)
            
    def cleanup(self) -> None:
        """
        Cleanup before new txt generation
        
        :rtype: None
        """
        self._initialize()