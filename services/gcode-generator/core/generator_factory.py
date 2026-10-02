from __future__ import annotations

from core.generator import Generator
from core.generators.gcode_generator import GcodeGenerator
from core.generators.svg_generator import SvgGenerator
from core.generators.txt_generator import TxtGenerator
from core.path_node import PathNode


class GeneratorFactory:
    """Factory for creating and managing Path( GCode & PointCloud ) generators"""

    def __init__(self) -> None:
        # Map file extensions to generator classes
        self._generators: dict[str, type[Generator]] = {
            "Gcode": GcodeGenerator,
            "TXT": TxtGenerator,
            "SVG": SvgGenerator
            # ".CNC": dotCNCGenerator,
            # "PointCloud": PointCloudGenerator,
            # Add more generators as needed
        }
        self._current_generator: Generator | None = None

    def create_generator(self, file_type: str | None, path_nodes: list[PathNode]) -> Generator:
        """Create a new generator of the specified type"""
        print(f"File type is {file_type}")
        
        if not file_type:
            file_type = "Gcode"
            
        if file_type not in self._generators:
            raise ValueError(f"Unsupported file type: {file_type}")

        # Cleanup existing generator if it exists
        if self._current_generator:
            self._current_generator.cleanup()

        # Create new generator
        generator_class = self._generators[file_type]
        self._current_generator = generator_class(path_nodes)
        return self._current_generator