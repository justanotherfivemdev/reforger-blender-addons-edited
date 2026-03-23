import bpy
from bpy.props import StringProperty, EnumProperty, IntProperty

from ..constants import GEAR_TYPE_ITEMS, GEAR_BONE_MAPPING, GEAR_LOD_RATIOS
from .gear_validate import validate_gear_objects


class CHARGEAR_OT_full_pipeline(bpy.types.Operator):
    """Run the full gear import pipeline: import → bind → LODs → collider → sort → validate"""
    bl_idname = "chargear.full_pipeline"
    bl_label = "Full Gear Pipeline"
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
    lod_levels: IntProperty(
        name="LOD Levels",
        description="Number of additional LOD levels to generate",
        default=3,
        min=1,
        max=4,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        summary = []

        # ── Step 1: Import ──────────────────────────────────────────────
        try:
            result = bpy.ops.chargear.import_gear(
                filepath=self.filepath,
                gear_type=self.gear_type,
                gear_name=self.gear_name,
            )
            if 'CANCELLED' in result:
                self.report({'ERROR'}, "Pipeline aborted: import step failed")
                return {'CANCELLED'}
            summary.append("✓ Import")
        except Exception as exc:
            self.report({'ERROR'}, f"Pipeline aborted at import step: {exc}")
            return {'CANCELLED'}

        # Find the imported LOD0 mesh
        lod0_name = f"{self.gear_name}_LOD0"
        lod0 = bpy.data.objects.get(lod0_name)
        if lod0 is None:
            self.report({'WARNING'}, f"Could not find '{lod0_name}' after import — skipping downstream steps")
            return {'FINISHED'}

        # ── Step 2: Bind to skeleton ────────────────────────────────────
        try:
            bpy.ops.object.select_all(action='DESELECT')
            lod0.select_set(True)
            context.view_layer.objects.active = lod0
            bpy.ops.chargear.bind_to_skeleton(gear_type=self.gear_type)
            summary.append("✓ Rig binding")
        except Exception as exc:
            self.report({'WARNING'}, f"Rig binding step failed (continuing): {exc}")
            summary.append("✗ Rig binding (failed)")

        # ── Step 3: Generate LODs ───────────────────────────────────────
        try:
            bpy.ops.object.select_all(action='DESELECT')
            lod0.select_set(True)
            context.view_layer.objects.active = lod0
            bpy.ops.chargear.create_gear_lods(lod_levels=self.lod_levels)
            summary.append(f"✓ LODs (x{self.lod_levels})")
        except Exception as exc:
            self.report({'WARNING'}, f"LOD generation step failed (continuing): {exc}")
            summary.append("✗ LODs (failed)")

        # ── Step 4: Generate collider ───────────────────────────────────
        try:
            bpy.ops.object.select_all(action='DESELECT')
            lod0.select_set(True)
            context.view_layer.objects.active = lod0
            bpy.ops.chargear.create_gear_collider()
            summary.append("✓ Collider")
        except Exception as exc:
            self.report({'WARNING'}, f"Collider generation step failed (continuing): {exc}")
            summary.append("✗ Collider (failed)")

        # ── Step 5: Sort into collections ───────────────────────────────
        try:
            bpy.ops.arvehicles.sort_into_collections()
            summary.append("✓ Sort into collections")
        except Exception as exc:
            self.report({'WARNING'}, f"Sort step failed (continuing): {exc}")
            summary.append("✗ Sort (failed)")

        # ── Step 6: Validate ────────────────────────────────────────────
        try:
            issues = validate_gear_objects(list(bpy.data.objects))
            errors = [m for sev, m in issues if sev == 'ERROR']
            warnings = [m for sev, m in issues if sev == 'WARNING']
            for sev, msg in issues:
                self.report({sev}, msg)
            summary.append(f"✓ Validation ({len(errors)} errors, {len(warnings)} warnings)")
        except Exception as exc:
            self.report({'WARNING'}, f"Validation step failed (continuing): {exc}")
            summary.append("✗ Validation (failed)")

        self.report({'INFO'}, "Pipeline complete: " + " | ".join(summary))
        return {'FINISHED'}
