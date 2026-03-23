import os
import bpy
from bpy.props import StringProperty, BoolProperty

from ..constants import CHAR_TEMPLATE_PREFIX


class CHARGEAR_OT_export_gear(bpy.types.Operator):
    """Export the prepared gear as an FBX file ready for Reforger Tools import"""
    bl_idname = "chargear.export_gear"
    bl_label = "Export Gear FBX"
    bl_options = {'REGISTER'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    apply_transforms: BoolProperty(
        name="Apply Transforms",
        description="Apply all transforms before export",
        default=True,
    )

    def invoke(self, context, event):
        # Default filename from the gear name property
        gear_name = getattr(context.scene, 'chargear_name', 'Gear') or 'Gear'
        self.filepath = gear_name + ".fbx"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No export path specified")
            return {'CANCELLED'}

        # Ensure .fbx extension
        if not self.filepath.lower().endswith('.fbx'):
            self.filepath += '.fbx'

        # Collect exportable objects (exclude character template objects)
        export_objects = [
            o for o in context.scene.objects
            if not o.name.startswith(CHAR_TEMPLATE_PREFIX)
        ]
        if not export_objects:
            self.report({'ERROR'}, "No objects to export")
            return {'CANCELLED'}

        # Select only the objects we want to export
        bpy.ops.object.select_all(action='DESELECT')
        for obj in export_objects:
            obj.select_set(True)

        # Apply transforms if requested
        if self.apply_transforms:
            for obj in export_objects:
                if obj.type in ('MESH', 'ARMATURE'):
                    # Apply transforms to this object only
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    context.view_layer.objects.active = obj
                    try:
                        bpy.ops.object.transform_apply(
                            location=False, rotation=True, scale=True)
                    except Exception as exc:
                        self.report(
                            {'WARNING'},
                            f"Failed to apply transforms to {obj.name}: {exc}",
                        )

        # Re-select after transform application
        bpy.ops.object.select_all(action='DESELECT')
        for obj in export_objects:
            obj.select_set(True)

        # Set active object to armature if available (FBX exporter preference)
        armature = next(
            (o for o in export_objects if o.type == 'ARMATURE'), None)
        if armature:
            context.view_layer.objects.active = armature

        # Export FBX with Enfusion-compatible settings
        # Aligned with the BK FBX Exporter conventions for Arma Reforger.
        try:
            bpy.ops.export_scene.fbx(
                filepath=self.filepath,
                use_selection=True,
                apply_scale_options='FBX_SCALE_ALL',
                axis_forward='Y',
                axis_up='Z',
                use_mesh_modifiers=True,
                mesh_smooth_type='FACE',
                use_subsurf=False,
                add_leaf_bones=False,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_armature_deform_only=False,
                bake_anim=False,
                use_custom_props=True,
            )
        except Exception as exc:
            self.report({'ERROR'}, f"FBX export failed: {exc}")
            return {'CANCELLED'}

        filename = os.path.basename(self.filepath)
        self.report({'INFO'}, f"Exported gear FBX: {filename}")
        return {'FINISHED'}
