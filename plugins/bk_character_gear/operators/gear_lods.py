import bpy
from bpy.props import IntProperty

from ..constants import GEAR_LOD_RATIOS


class CHARGEAR_OT_create_gear_lods(bpy.types.Operator):
    """Generate LOD meshes for the selected gear mesh"""
    bl_idname = "chargear.create_gear_lods"
    bl_label = "Create Gear LODs"
    bl_options = {'REGISTER', 'UNDO'}

    lod_levels: IntProperty(
        name="LOD Levels",
        description="Number of additional LOD levels to generate (beyond LOD0)",
        default=3,
        min=1,
        max=4,
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Use the first selected mesh as the LOD0 source
        source = mesh_objects[0]

        # Determine base name (strip any existing _LOD0 suffix)
        base_name = source.name
        if base_name.upper().endswith("_LOD0"):
            base_name = base_name[:-5]

        # Ensure source is named _LOD0
        if not source.name.upper().endswith("_LOD0"):
            source.name = f"{base_name}_LOD0"
            if source.data:
                source.data.name = f"{base_name}_LOD0"

        ratios = GEAR_LOD_RATIOS[:self.lod_levels]
        created = []

        for i, ratio in enumerate(ratios):
            lod_level = i + 1
            lod_name = f"{base_name}_LOD{lod_level}"

            # Duplicate source
            new_data = source.data.copy()
            new_obj = source.copy()
            new_obj.data = new_data
            new_obj.name = lod_name
            new_obj.data.name = lod_name

            # Link to same collections as source
            for col in source.users_collection:
                col.objects.link(new_obj)

            # Copy armature modifiers from source so LODs stay rigged
            for mod in source.modifiers:
                if mod.type == 'ARMATURE':
                    new_mod = new_obj.modifiers.new(name=mod.name, type='ARMATURE')
                    new_mod.object = mod.object

            # Apply decimate modifier
            dec_mod = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
            dec_mod.ratio = ratio
            dec_mod.use_collapse_triangulate = False

            context.view_layer.objects.active = new_obj
            try:
                bpy.ops.object.modifier_apply(modifier=dec_mod.name)
            except Exception as exc:
                self.report({'WARNING'}, f"Could not apply decimate to '{lod_name}': {exc}")
                new_obj.modifiers.remove(dec_mod)

            created.append(lod_name)

        self.report({'INFO'}, f"Created {len(created)} LOD level(s): {', '.join(created)}")
        return {'FINISHED'}
