from dataclasses import dataclass
from typing import ClassVar

import numpy as np

from core.path_node import PathNode
from core.point import Point


@dataclass
class GUICalc:
    # The angle at which the scribe is rotated from the input
    rotation: np.float64
    # The generated path for Matplotlib
    path: list[PathNode]


@dataclass
class LaserData:
    is_p1: bool
    isolation_line_enabled: bool
    # Speed when laser is on, mm/s
    scribing_speed: float
    # Speed when laser is off, 140 mm/s
    translation_speed: float = 140
    # 30 µm == 0.03 mm
    laser_thickness: float = 0.03


@dataclass
class PanelData:
    # Square panel, 300 mm
    panel_width: float = 300
    panel_height: float = 300
    # Border kept clear of scribes on every side of the panel, mm
    edge_margin: float = 0.0


@dataclass
class CellParameters:
    # Number of cells in a panel
    cell_count: int
    # Dimensions of the cells
    cell_length: float
    cell_width: float
    # Starting position of the scribe
    origin: Point
    default_pass_gap: float = 0.02


@dataclass
class P1Specific:
    isolation_line_spacing: float
    # Speed when scribing isolation lines, 140 mm/s
    isolation_line_speed: float = 140


@dataclass
class P2Specific:
    # Gap between passes for a line
    pass_gap: float
    # Number of passes for a line
    pass_count: int
    line_width: float
    initial_offset: float
    # Found offsets
    offset_a: float
    offset_b: float
    #distance between offset_a and offset_b
    offset_length: float
    # Clearance between the last cell's P2 scribe and the inner edge of the second bus bar
    # (mirrors p2_bus_spacing at the first bus bar)
    bus_bar_spacing: float
    # Width of bus bar
    bus_bar_width: float
    # Clearance between the first cell's P2 scribe and the inner edge of the first bus bar
    p2_bus_spacing: float
    # Speed when scribing bus bar, 140 mm/s
    bus_bar_speed: float = 140


@dataclass
class FileInformation:
    # The final output, generally gcode
    generated_output: str
    filename: str
    # File extension, e.g. ".exe"
    file_extension: str
    # The file path, e.g. "C:/Users/Admin/Downloads/LaserGcode.exe"
    file_path: str
    # The type of the file to make, e.g. "Gcode"
    filetype: str
    file_type_dict: ClassVar[dict[str, str]] = {
        "Gcode": ".gcode",
        "TXT": ".txt",
        "SVG": ".svg"
    }
    debug_mode: bool


@dataclass
class SolarData:
    """
    Holds all other data classes for easy movement in the controller.
    """
    gui_calc: GUICalc
    laser_data: LaserData
    panel_data: PanelData
    cell_parameters: CellParameters
    p1_specific: P1Specific
    p2_specific: P2Specific
    file_information: FileInformation