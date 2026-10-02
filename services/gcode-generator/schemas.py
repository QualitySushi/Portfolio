from __future__ import annotations

from pydantic import BaseModel, Field


class SaveRequest(BaseModel):
    user_id: str
    file_type: str
    output_data: str


class GenerationRequest(BaseModel):
    # Metadata & General Settings
    user_id: str | None = Field(default=None, description="User identifier or context")
    file_type: str = Field(default="Gcode", description="Output format: 'Gcode', 'TXT', or 'SVG'")
    
    # Cell Parameters (CellParameters)
    cell_count: int = Field(default=6, description="Total number of solar cells")
    cell_width: float = Field(default=50.0, description="Width of an individual cell in mm")
    cell_length: float = Field(default=300.0, description="Length of an individual cell in mm")
    origin_x: float = Field(default=0.0, description="X coordinate origin offset")
    origin_y: float = Field(default=0.0, description="Y coordinate origin offset")
    default_pass_gap: float = Field(default=0.05, description="Default fallback gap spacing between passes")

    # Isolation Pass / P1 Settings (P1Specific)
    isolation_line_enabled: bool = Field(default=True, description="Whether to include the P1 isolation pass")
    isolation_spacing: float = Field(default=1.0, description="Spacing distance between isolation lines")

    # Bus Bars & Scribing / P2 Settings (P2Specific & LaserData flags)
    is_p1: bool = Field(default=True, description="True for P1 isolation/cells, False for P2 bus bars/scribing")
    bus_bar_spacing: float = Field(default=50.0, description="Spacing offset for the second bus bar")
    p2_bus_spacing: float = Field(default=0.0, description="Spacing offset for the first bus bar")
    bus_bar_width: float = Field(default=2.0, description="Overall width of the bus bar")
    pass_gap: float = Field(default=0.05, description="Gap offset between scribing passes")
    pass_count: int = Field(default=2, description="Number of passes to perform for a cell edge or feature")
    initial_offset: float = Field(default=0.0, description="Initial Y translation offset for P2 cells")

    # Laser & Motion Parameters (LaserData)
    speed: float = Field(default=15000.0, description="Translation speed of the laser when beam is off")
    scribing_speed: float = Field(default=140.0, description="Active cutting speed of the laser when beam is on")

    # Global / Workspace Settings
    rotation: float = Field(default=0.0, description="Rotation angle in degrees for the generated path")
    panel_max_size: float = Field(default=300.0, description="Maximum bounding size of the square solar panel workspace")
    debug_mode: bool = Field(default=True, description="Enables detailed file and console logging")