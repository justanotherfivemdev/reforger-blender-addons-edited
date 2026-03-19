import bpy
from bpy.types import Operator


class MESH_OT_crater_reset_defaults(Operator):
    """Reset all crater properties to their default values"""
    bl_idname = "mesh.crater_reset_defaults"
    bl_label = "Reset to Defaults"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.crater_properties
        for prop_name in props.bl_rna.properties.keys():
            if prop_name == 'rna_type':
                continue
            try:
                props.property_unset(prop_name)
            except Exception:
                pass
        return {'FINISHED'}
