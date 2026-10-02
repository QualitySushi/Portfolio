import numpy as np

from core.generator_factory import GeneratorFactory
from core.path_generator import PathGenerator
from core.point import Point
from core.solar_data import (
    CellParameters,
    FileInformation,
    GUICalc,
    LaserData,
    P1Specific,
    P2Specific,
    PanelData,
    SolarData,
)


class GCodeService:
    @staticmethod
    def process_generation(payload) -> str:
        # 1. Map incoming payload fields into your structured dataclasses
        cell_parameters = CellParameters(
            cell_count=getattr(payload, "cell_count", 10),
            cell_length=getattr(payload, "cell_length", 150.0),
            cell_width=getattr(payload, "cell_width", 50.0),
            origin=Point(payload.origin_x, payload.origin_y),
            default_pass_gap=getattr(payload, "default_pass_gap", 0.02)
        )

        laser_data = LaserData(
            is_p1=getattr(payload, "is_p1", True),
            isolation_line_enabled=getattr(payload, "isolation_line_enabled", True),
            scribing_speed=getattr(payload, "scribing_speed", payload.speed),
            translation_speed=getattr(payload, "translation_speed", 140.0),
            laser_thickness=getattr(payload, "laser_thickness", 0.03)
        )

        # The form sends the panel size as panel_max_size. (Reading panel_width/panel_height here meant the value the
        # form sent was ignored and the 300 mm default was always used.)
        panel_size = getattr(payload, "panel_max_size", 300.0)
        panel_data = PanelData(
            panel_width=panel_size,
            panel_height=panel_size,
            edge_margin=getattr(payload, "edge_margin", 0.0)
        )

        # The form sends this as isolation_spacing. (Reading isolation_line_spacing here meant the value the form
        # sent was ignored and the 1.0 default was always used.)
        p1_specific = P1Specific(
            isolation_line_spacing=getattr(payload, "isolation_spacing", 1.0),
            isolation_line_speed=getattr(payload, "isolation_line_speed", 140.0)
        )

        p2_specific = P2Specific(
            pass_gap=getattr(payload, "pass_gap", 0.05),
            pass_count=getattr(payload, "pass_count", 2),
            line_width=getattr(payload, "line_width", 0.1),
            initial_offset=getattr(payload, "initial_offset", 0.0),
            offset_a=getattr(payload, "offset_a", 0.0),
            offset_b=getattr(payload, "offset_b", 0.0),
            offset_length=getattr(payload, "offset_length", 0.0),
            bus_bar_spacing=getattr(payload, "bus_bar_spacing", 50.0), # Updated default
            bus_bar_width=getattr(payload, "bus_bar_width", 2.0),     # Updated default
            p2_bus_spacing=getattr(payload, "p2_bus_spacing", 10.0),   # Updated default
            bus_bar_speed=getattr(payload, "bus_bar_speed", 140.0)
        )

        gui_calc = GUICalc(
            rotation=np.float64(getattr(payload, "rotation", 0.0)),
            path=[]
        )

        file_information = FileInformation(
            generated_output="",
            filename=getattr(payload, "filename", "output"),
            file_extension=FileInformation.file_type_dict.get(payload.file_type, ".gcode"),
            file_path="",
            filetype=payload.file_type,
            debug_mode=getattr(payload, "debug_mode", False)
        )

        # 2. Bundle everything into your main SolarData container container
        solar_data = SolarData(
            gui_calc=gui_calc,
            laser_data=laser_data,
            panel_data=panel_data,
            cell_parameters=cell_parameters,
            p1_specific=p1_specific,
            p2_specific=p2_specific,
            file_information=file_information
        )

        # 3. Instantiate and run your PathGenerator to get the actual path nodes
        path_gen = PathGenerator(
            cell_parameters=solar_data.cell_parameters,
            p1_specific=solar_data.p1_specific,
            p2_specific=solar_data.p2_specific,
            laser_data=solar_data.laser_data,
            rotation=solar_data.gui_calc.rotation,
            panel_max_size=solar_data.panel_data.panel_width,
            debug_mode=solar_data.file_information.debug_mode,
            edge_margin=solar_data.panel_data.edge_margin
        )
        
        nodes = path_gen.generate_path()

        if not nodes:
            raise ValueError("Path generation resulted in an empty node list.")

        # 4. Hand the generated nodes to the factory to export the final file format (G-code, SVG, etc.)
        factory = GeneratorFactory()
        generator = factory.create_generator(payload.file_type, nodes)
        return generator.generate()