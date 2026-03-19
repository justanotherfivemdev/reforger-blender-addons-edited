import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty, BoolProperty


class CraterProperties(PropertyGroup):
    """Properties for crater generation"""

    outer_radius: FloatProperty(
        name="Outer Radius",
        description="Total footprint radius of the crater",
        default=5.0,
        min=0.5,
        max=100.0,
        unit='LENGTH',
        step=10
    )

    rim_radius: FloatProperty(
        name="Rim Radius",
        description="Radius of the rim peak (typically 35-55% of outer radius)",
        default=2.25,
        min=0.1,
        max=50.0,
        unit='LENGTH',
        step=10
    )

    rim_height: FloatProperty(
        name="Rim Height",
        description="Height of the rim above ground level",
        default=0.5,
        min=0.0,
        max=100.0,
        unit='LENGTH',
        step=10
    )

    depth: FloatProperty(
        name="Depth",
        description="Bowl depth below ground level",
        default=0.5,
        min=0.01,
        max=100.0,
        unit='LENGTH',
        step=10
    )

    resolution: IntProperty(
        name="Resolution",
        description="Number of vertices per ring (higher = more detail)",
        default=32,
        min=8,
        max=512,
        step=4
    )

    noise_strength: FloatProperty(
        name="Surface Noise",
        description="Subtle surface irregularity",
        default=0.02,
        min=0.0,
        max=5.0,
        step=1
    )

    create_materials: BoolProperty(
        name="Create Materials",
        description="Generate inner/outer crater materials",
        default=True
    )

    auto_uv: BoolProperty(
        name="Auto UV",
        description="Generate UV mapping",
        default=True
    )
