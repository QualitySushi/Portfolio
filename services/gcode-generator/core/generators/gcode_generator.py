from __future__ import annotations

from core.generator import Generator
from core.path_node import PathNode


class GcodeGenerator(Generator):

    def _initialize(self) -> None:
        """Initialize GCode-specific settings"""
        self._commands: list[str] = []
        self._current_x: float | None = None
        self._current_y: float | None = None
        self._last_set_speed: float | None = None
        self._current_beam_state: bool | None = False

    def generate(self) -> str:
        """Generate GCode from path nodes"""

        self.cleanup()

        self._commands.append("G90")  # Absolute positioning
        
        current_line_type: str | None = None

        # Process each path node
        for node in self._path_nodes:

            # Inject a comment if the line type changes (great for readability/debugging)
            if node.line_type and node.line_type != current_line_type:
                current_line_type = node.line_type
                self._commands.append(f"\n; --- Path Type: {current_line_type.upper()} ---")

            # Update beam state if changed
            if node.beam_state != self._current_beam_state:
                self._add_beam_command(node.beam_state)

            # Update position if changed
            if node.pos.x != self._current_x or node.pos.y != self._current_y:
                self._add_move(node)

        # Ensure beam is off at end
        if self._current_beam_state:
            self._add_beam_command(False)

        # Job end
        self._commands.append("M2")
        self._commands.append("M5")

        return "\n".join(self._commands)

    def _add_move(self, node: PathNode) -> None:
        """Add a movement command with appropriate speed"""
        # Use G0 for rapid moves (beam off), G1 for scribing moves (beam on)
        # NOTE: some controllers allow specifying feed rate (F) for G0.
        command_parts = ["G0" if not node.beam_state else "G1"]

        # Add coordinates that have changed
        pos_changed = False
        if node.pos.x != self._current_x:
            command_parts.append(f"X{node.pos.x:.4f}")
            self._current_x = node.pos.x
            pos_changed = True

        if node.pos.y != self._current_y:
            command_parts.append(f"Y{node.pos.y:.4f}")
            self._current_y = node.pos.y
            pos_changed = True

        # Incoming speed is in mm/sec though GCode uses mm/min.
        if (node.approach_speed * 60) != self._last_set_speed:
            speed_val = float(node.approach_speed * 60)  # Multiply by 60 to ensure the new speed is mm/min
            command_parts.append(f"F{speed_val:.2f}")
            self._last_set_speed = speed_val

            # Only add the command if there's a positional move
        if pos_changed:
            self._commands.append(" ".join(command_parts))

    def _add_beam_command(self, beam_state: bool) -> None:
        """Add a beam on/off command"""
        # Using M3/M5 for laser control
        # M3 = beam on, M5 = beam off
        self._commands.append("M3" if beam_state else "M5")
        self._current_beam_state = beam_state

    def cleanup(self) -> None:
        """Cleanup before new gcode generation by re-initializing state."""
        self._initialize()