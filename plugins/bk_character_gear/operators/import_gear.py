import bpy
from bpy.props import StringProperty, EnumProperty

from ..constants import GEAR_TYPE_ITEMS, GEAR_BONE_MAPPING, CHARACTER_SKELETON_BONES


class CHARGEAR_OT_import_gear(bpy.types.Operator):
    """Import a gear FBX and normalise it for the Arma Reforger pipeline"""
    bl_idname = "chargear.import_gear"
    bl_label = "Import Gear FBX"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.fbx;*.glb;*.gltf", options={'HIDDEN'})

    gear_type: EnumProperty(
        name="Gear Type",
        items=GEAR_TYPE_ITEMS,
        default='HEADGEAR',
    )
    gear_name: StringProperty(
        name="Gear Name",
        description="Base name for the asset (e.g. Ops_Core_Helmet)",
        default="Gear",
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        import os

        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}

        ext = os.path.splitext(self.filepath)[1].lower()
        if ext not in ('.fbx', '.glb', '.gltf'):
            self.report({'ERROR'}, f"Unsupported file format: {ext}")
            return {'CANCELLED'}

        # Record objects present before import
        before = set(bpy.data.objects)

        # Import the file
        try:
            if ext == '.fbx':
                bpy.ops.import_scene.fbx(
                    filepath=self.filepath,
                    automatic_bone_orientation=True,
                    axis_forward='Y',
                    axis_up='Z',
                )
            else:
                bpy.ops.import_scene.gltf(filepath=self.filepath)
        except Exception as exc:
            self.report({'ERROR'}, f"Import failed: {exc}")
            return {'CANCELLED'}

        imported = [o for o in bpy.data.objects if o not in before]
        if not imported:
            self.report({'WARNING'}, "No objects were imported")
            return {'CANCELLED'}

        # Separate mesh objects from armatures
        imported_meshes = [o for o in imported if o.type == 'MESH']
        imported_armatures = [o for o in imported if o.type == 'ARMATURE']

        warnings = []

        # Apply transforms and rename meshes
        for idx, mesh_obj in enumerate(imported_meshes):
            bpy.ops.object.select_all(action='DESELECT')
            mesh_obj.select_set(True)
            context.view_layer.objects.active = mesh_obj

            # Apply all transforms
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            # Set origin to geometry center
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

            # Rename: first mesh gets _LOD0, additional ones _LOD0_part1, etc.
            new_name = f"{self.gear_name}_LOD0" if idx == 0 else f"{self.gear_name}_LOD0_part{idx}"
            mesh_obj.name = new_name
            if mesh_obj.data:
                mesh_obj.data.name = new_name

        # Ensure metric units
        scene = context.scene
        if scene.unit_settings.system != 'METRIC':
            scene.unit_settings.system = 'METRIC'
            scene.unit_settings.scale_length = 1.0

        # Validate armature bone names if one was imported
        if imported_armatures:
            arm_obj = imported_armatures[0]
            imported_bone_names = {b.name for b in arm_obj.data.bones}
            unknown = imported_bone_names - set(CHARACTER_SKELETON_BONES)
            if unknown:
                warnings.append(
                    f"Imported armature has unrecognised bones: {', '.join(sorted(unknown))}"
                )
        else:
            # No armature in FBX — create a minimal one from the gear bone mapping
            relevant_bones = GEAR_BONE_MAPPING.get(self.gear_type, [])
            if relevant_bones:
                arm_data = bpy.data.armatures.new(f"{self.gear_name}_Armature")
                arm_obj = bpy.data.objects.new(f"{self.gear_name}_Armature", arm_data)
                context.collection.objects.link(arm_obj)

                context.view_layer.objects.active = arm_obj
                arm_obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')

                for bone_name in relevant_bones[:1]:  # Root bone at origin
                    eb = arm_data.edit_bones.new(bone_name)
                    eb.head = (0.0, 0.0, 0.0)
                    eb.tail = (0.0, 0.1, 0.0)

                bpy.ops.object.mode_set(mode='OBJECT')
                warnings.append(
                    f"No armature in FBX — created minimal stub with {len(relevant_bones[:1])} bone(s). "
                    "Use 'Bind to Skeleton' after providing the full character armature."
                )

        # Report
        msg_parts = [f"Imported {len(imported_meshes)} mesh(es) as '{self.gear_name}_LOD0'"]
        for w in warnings:
            self.report({'WARNING'}, w)
            msg_parts.append(f"Warning: {w}")

        self.report({'INFO'}, msg_parts[0])
        return {'FINISHED'}
