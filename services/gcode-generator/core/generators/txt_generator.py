from __future__ import annotations

from core.generator import Generator
from core.path_node import PathNode


class TxtGenerator(Generator):
    """Generator for producing TXT command output from path nodes"""

    # Note: Speed, Acceleration and set-origin to be confirmed if useful.

    def _initialize(self) -> None:
        """Initialize TXT-specific settings"""
        self._commands: list[str] = []
        self._current_x: float | None = None
        self._current_y: float | None = None
        self._last_set_speed: float | None = None
        self._current_beam_state: bool | None = False

    def generate(self) -> str:
        """Generate TXT format commands from path nodes"""
        self.cleanup()

        # Set initial parameters
        # self._commands.append("SET_ORIGIN 0 0")  # Set the origin
        # initial_speed_mm_sec = self._movement_speed / 60
        # self._commands.append(f"SET_SPEED {initial_speed_mm_sec:.2f}")
        # self._current_speed = initial_speed_mm_sec  # Set initial current speed

        # self._commands.append("SET_ACCEL 500")  # Set default acceleration

        # Process each path node
        for node in self._path_nodes:
            # Update beam state if changed
            if node.beam_state != self._current_beam_state:
                self._add_beam_command(node.beam_state)

            # Update position if changed
            if node.pos.x != self._current_x or node.pos.y != self._current_y:
                self._add_move(node)

        # Ensure beam is off at end
        self._add_beam_command(False)

        return "\n".join(self._commands)

    def _add_move(self, node: PathNode) -> None:
        """Add a movement command with appropriate speed"""

        if node.approach_speed != self._last_set_speed:
            self._commands.append(f"SET_SPEED {node.approach_speed:.2f}")
            self._last_set_speed = node.approach_speed

        # Use GOTO for absolute positioning
        if node.pos.x != self._current_x or node.pos.y != self._current_y:
            self._commands.append(f"GOTO {node.pos.x:.4f} {node.pos.y:.4f}")
            self._current_x = node.pos.x
            self._current_y = node.pos.y

    def _add_beam_command(self, beam_state: bool) -> None:
        """Add a beam on/off command"""
        self._commands.append("BEAM_ON" if beam_state else "BEAM_OFF")
        self._current_beam_state = beam_state

    def cleanup(self) -> None:
        """Cleanup before new txt generation"""
        self._initialize()