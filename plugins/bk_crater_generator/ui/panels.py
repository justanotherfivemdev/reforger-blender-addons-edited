import bpy
from bpy.types import Panel


class VIEW3D_PT_crater_generator(Panel):
    """Crater generator panel"""
    bl_label = "Game Crater Generator"
    bl_idname = "VIEW3D_PT_crater_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create"

    def draw(self, context):
        layout = self.layout
        props = context.scene.crater_properties

        # Generate button
        row = layout.row()
        row.scale_y = 1.8
        op = row.operator("mesh.add_crater", text="Generate Crater", icon='OUTLINER_OB_META')
        op.outer_radius = props.outer_radius
        op.rim_radius = props.rim_radius
        op.rim_height = props.rim_height
        op.depth = props.depth
        op.resolution = props.resolution
        op.noise_strength = props.noise_strength
        op.create_materials = props.create_materials
        op.auto_uv = props.auto_uv

        # Reset button
        row = layout.row()
        row.operator("mesh.crater_reset_defaults", text="Reset to Defaults", icon='LOOP_BACK')

        layout.separator()

        # Game integration
        box = layout.box()
        box.label(text="Game Integration", icon='TOOL_SETTINGS')
        col = box.column(align=True)
        col.operator("mesh.crater_create_firegeo_collision",
                     text="Create FireGeo Collision", icon='PHYSICS')
        col.operator("mesh.crater_create_lods",
                     text="Create LOD Levels", icon='MOD_DECIM')

        layout.separator()

        # Dimensions
        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CIRCLE')
        col = box.column(align=True)
        col.prop(props, "outer_radius")
        col.prop(props, "rim_radius")
        col.prop(props, "rim_height")
        col.prop(props, "depth")
        col.prop(props, "resolution")
        estimated_tris = props.resolution * 11  # ~11 tris per resolution step
        box.label(text=f"~{estimated_tris} triangles", icon='INFO')

        # Surface
        box = layout.box()
        box.label(text="Surface", icon='TEXTURE')
        box.prop(props, "noise_strength")

        # Output
        box = layout.box()
        box.label(text="Output", icon='EXPORT')
        col = box.column(align=True)
        col.prop(props, "create_materials")
        col.prop(props, "auto_uv")

        # Material blending
        box = layout.box()
        box.label(text="Material Blend", icon='NODE_MATERIAL')
        box.label(text="Select faces in Edit Mode, then assign:", icon='INFO')
        row = box.row(align=True)
        op0 = row.operator("mesh.crater_assign_material", text="Assign Mat 0", icon='MATERIAL')
        op0.mat_index = 0
        op1 = row.operator("mesh.crater_assign_material", text="Assign Mat 1", icon='MATERIAL')
        op1.mat_index = 1
        box.separator()
        box.operator("mesh.crater_blend_materials",
                     text="Blend Material Seam", icon='SMOOTHCURVE')


classes = (
    VIEW3D_PT_crater_generator,
)
