import bpy
import bmesh
from bpy.types import Operator
from bpy.props import IntProperty


class MESH_OT_crater_assign_material(Operator):
    """Assign a crater material slot to selected faces"""
    bl_idname = "mesh.crater_assign_material"
    bl_label = "Assign Crater Material"
    bl_options = {'REGISTER', 'UNDO'}

    mat_index: IntProperty(name="Material Index", default=0, min=0, max=1)

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if len(obj.data.materials) < self.mat_index + 1:
            self.report({'ERROR'}, f"Mesh has no material in slot {self.mat_index}")
            return {'CANCELLED'}

        if obj.mode != 'EDIT':
            self.report({'ERROR'}, "Must be in Edit Mode with faces selected")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        assigned = 0
        for face in bm.faces:
            if face.select:
                face.material_index = self.mat_index
                assigned += 1

        bmesh.update_edit_mesh(obj.data)
        self.report({'INFO'}, f"Assigned material {self.mat_index} to {assigned} faces")
        return {'FINISHED'}
