from abc import ABC, abstractmethod

from core.path_node import PathNode


class Generator(ABC):
    """Abstract base class for GCode generators"""

    def __init__(self, path_nodes: list[PathNode]):
        self._path_nodes = path_nodes
        self._movement_speed = 140  # mm/min
        self._scribing_speed = 5  # mm/min
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """Initialize generator-specific settings"""

    @abstractmethod
    def generate(self) -> str:
        """Generate GCode from path nodes"""

    def cleanup(self) -> None:
        """Cleanup resources before generator destruction"""