import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty

from ..constants import GEAR_TYPE_ITEMS, GEAR_BONE_MAPPING


class CHARGEAR_OT_bind_to_skeleton(bpy.types.Operator):
    """Bind the selected gear mesh to the character skeleton"""
    bl_idname = "chargear.bind_to_skeleton"
    bl_label = "Bind to Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    gear_type: EnumProperty(
        name="Gear Type",
        items=GEAR_TYPE_ITEMS,
        default='HEADGEAR',
    )

    def execute(self, context):
        # Find the armature in the scene
        armature = None
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break

        if not armature:
            self.report({'ERROR'}, "No armature found in the scene. Import or create a character armature first.")
            return {'CANCELLED'}

        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        relevant_bones = GEAR_BONE_MAPPING.get(self.gear_type, [])
        armature_bone_names = {b.name for b in armature.data.bones}
        valid_bones = [b for b in relevant_bones if b in armature_bone_names]

        if not valid_bones and self.gear_type != 'ACCESSORY':
            self.report({'WARNING'}, f"None of the expected bones for '{self.gear_type}' are present in the armature.")

        bound = 0
        for mesh_obj in mesh_objects:
            # Ensure armature modifier exists
            arm_mod = None
            for mod in mesh_obj.modifiers:
                if mod.type == 'ARMATURE':
                    arm_mod = mod
                    break
            if arm_mod is None:
                arm_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
            arm_mod.object = armature

            if self.gear_type == 'HEADGEAR':
                # Rigid binding: all verts → Head bone at weight 1.0
                head_bone = "Head"
                if head_bone in armature_bone_names:
                    if head_bone not in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups.new(name=head_bone)
                    vg = mesh_obj.vertex_groups[head_bone]
                    all_verts = [v.index for v in mesh_obj.data.vertices]
                    vg.add(all_verts, 1.0, 'REPLACE')
                else:
                    self.report({'WARNING'}, "Armature does not have a 'Head' bone — rigid bind skipped.")
            elif self.gear_type in ('VEST', 'FULL_BODY', 'PANTS', 'BOOTS', 'BACKPACK', 'GLOVES'):
                # Automatic weights via Blender's parent_set
                bpy.ops.object.select_all(action='DESELECT')
                mesh_obj.select_set(True)
                armature.select_set(True)
                context.view_layer.objects.active = armature
                try:
                    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
                except Exception as exc:
                    self.report({'WARNING'}, f"Auto-weight failed for '{mesh_obj.name}': {exc}")
            else:
                # ACCESSORY — assign all verts to first valid bone or leave unweighted
                if valid_bones:
                    bone_name = valid_bones[0]
                    if bone_name not in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups.new(name=bone_name)
                    vg = mesh_obj.vertex_groups[bone_name]
                    all_verts = [v.index for v in mesh_obj.data.vertices]
                    vg.add(all_verts, 1.0, 'REPLACE')

            # Validate vertex groups against armature bones
            orphaned = [vg.name for vg in mesh_obj.vertex_groups if vg.name not in armature_bone_names]
            if orphaned:
                self.report({'WARNING'}, f"'{mesh_obj.name}' has orphaned vertex groups: {', '.join(orphaned)}")

            bound += 1

        self.report({'INFO'}, f"Bound {bound} mesh(es) to skeleton using '{self.gear_type}' mode")
        return {'FINISHED'}


class CHARGEAR_OT_transfer_weights(bpy.types.Operator):
    """Transfer weights from a reference mesh to the selected gear mesh"""
    bl_idname = "chargear.transfer_weights"
    bl_label = "Transfer Weights"
    bl_options = {'REGISTER', 'UNDO'}

    source_object: StringProperty(
        name="Source Object",
        description="Name of the reference mesh to transfer weights from",
        default="",
    )

    def execute(self, context):
        if not self.source_object:
            self.report({'ERROR'}, "No source object specified")
            return {'CANCELLED'}

        source = bpy.data.objects.get(self.source_object)
        if source is None or source.type != 'MESH':
            self.report({'ERROR'}, f"Source object '{self.source_object}' not found or is not a mesh")
            return {'CANCELLED'}

        targets = [o for o in context.selected_objects if o.type == 'MESH' and o != source]
        if not targets:
            self.report({'ERROR'}, "No target mesh objects selected")
            return {'CANCELLED'}

        transferred = 0
        for target in targets:
            # Add Data Transfer modifier
            mod = target.modifiers.new(name="DataTransfer_Weights", type='DATA_TRANSFER')
            mod.object = source
            mod.use_vert_data = True
            mod.data_types_verts = {'VGROUP_WEIGHTS'}
            mod.vert_mapping = 'NEAREST'

            # Apply the modifier
            context.view_layer.objects.active = target
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                transferred += 1
            except Exception as exc:
                self.report({'WARNING'}, f"Could not apply weight transfer to '{target.name}': {exc}")
                target.modifiers.remove(mod)

        self.report({'INFO'}, f"Transferred weights to {transferred} object(s) from '{self.source_object}'")
        return {'FINISHED'}
