import bpy
import re


class CHARGEAR_PT_panel(bpy.types.Panel):
    bl_label = "BK Character Gear"
    bl_idname = "CHARGEAR_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BK Character Gear'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ============================================================
        # GEAR TYPE
        # ============================================================
        box = layout.box()
        box.label(text="Gear Type", icon='ARMATURE_DATA')
        box.prop(scene, "chargear_type", text="")
        box.prop(scene, "chargear_name", text="Name")

        # ============================================================
        # IMPORT
        # ============================================================
        box = layout.box()
        box.label(text="Import", icon='IMPORT')
        op = box.operator("chargear.import_gear", text="Import Gear FBX", icon='FILE_FOLDER')
        op.gear_type = scene.chargear_type
        op.gear_name = scene.chargear_name

        # ============================================================
        # ONE-CLICK PIPELINE
        # ============================================================
        box = layout.box()
        box.label(text="One-Click Pipeline", icon='PLAY')
        op = box.operator("chargear.full_pipeline", text="Full Gear Pipeline", icon='SHADERFX')
        op.gear_type = scene.chargear_type
        op.gear_name = scene.chargear_name

        # ============================================================
        # RIGGING
        # ============================================================
        box = layout.box()
        box.label(text="Rigging", icon='BONE_DATA')
        col = box.column(align=True)
        op = col.operator("chargear.bind_to_skeleton", text="Bind to Skeleton", icon='OUTLINER_OB_ARMATURE')
        op.gear_type = scene.chargear_type
        col.operator("chargear.transfer_weights", text="Transfer Weights", icon='WPAINT_HLT')

        # ============================================================
        # LODs
        # ============================================================
        box = layout.box()
        box.label(text="LODs", icon='MOD_DECIM')
        box.operator("chargear.create_gear_lods", text="Create Gear LODs", icon='TRIA_DOWN_BAR')

        # ============================================================
        # COLLISION
        # ============================================================
        box = layout.box()
        box.label(text="Collision", icon='MESH_CUBE')
        row = box.row(align=True)
        row.operator("chargear.create_gear_collider",      text="Trimesh (UTM_)",  icon='MOD_SOLIDIFY')
        row.operator("chargear.create_primitive_collider", text="Primitive (UBX_)", icon='MESH_CUBE')

        # ============================================================
        # VALIDATION
        # ============================================================
        box = layout.box()
        box.label(text="Validation", icon='CHECKMARK')
        box.operator("chargear.validate_gear", text="Validate Gear", icon='VIEWZOOM')

        # ============================================================
        # INFO
        # ============================================================
        box = layout.box()
        box.label(text="Info", icon='INFO')
        col = box.column(align=True)
        col.label(text=f"Name: {scene.chargear_name or '(not set)'}")
        col.label(text=f"Type: {scene.chargear_type}")

        # Count existing LOD levels
        lod_pattern = re.compile(rf'^{re.escape(scene.chargear_name)}_LOD(\d+)$', re.IGNORECASE) if scene.chargear_name else None
        if lod_pattern:
            lod_levels = sorted(
                int(m.group(1))
                for o in bpy.data.objects
                if o.type == 'MESH' and (m := lod_pattern.match(o.name))
            )
            if lod_levels:
                col.label(text=f"LODs: LOD{min(lod_levels)}–LOD{max(lod_levels)} ({len(lod_levels)} level(s))")
            else:
                col.label(text="LODs: none found")

        if scene.chargear_template_path:
            col.label(text="Template: set")
        else:
            col.label(text="Template: (none)")
