import bpy
from bpy.props import IntProperty, BoolProperty

from ..constants import GEAR_LOD_RATIOS, SHADOW_LOD_RATIO, VIEW_LOD_RATIO


def _duplicate_and_decimate(context, source, name, ratio, triangulate=False):
    """Duplicate *source*, decimate to *ratio*, and return the new object."""
    new_data = source.data.copy()
    new_obj = source.copy()
    new_obj.data = new_data
    new_obj.name = name
    new_obj.data.name = name

    for col in source.users_collection:
        col.objects.link(new_obj)

    dec_mod = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
    dec_mod.ratio = ratio
    dec_mod.use_collapse_triangulate = triangulate

    context.view_layer.objects.active = new_obj
    try:
        bpy.ops.object.modifier_apply(modifier=dec_mod.name)
    except Exception as exc:
        new_obj.modifiers.remove(dec_mod)
        raise exc

    return new_obj


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

    create_shadow_lod: BoolProperty(
        name="Shadow LOD",
        description="Generate a very low-poly Shadow LOD for shadow rendering",
        default=True,
    )

    create_view_lod: BoolProperty(
        name="View LOD",
        description="Generate an optional simplified View LOD for extreme distances",
        default=False,
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

        # ── Standard LODs ───────────────────────────────────────────────
        for i, ratio in enumerate(ratios):
            lod_level = i + 1
            lod_name = f"{base_name}_LOD{lod_level}"

            try:
                _duplicate_and_decimate(context, source, lod_name, ratio)
                created.append(lod_name)
            except Exception as exc:
                self.report({'WARNING'}, f"Could not apply decimate to '{lod_name}': {exc}")

        # ── Shadow LOD ──────────────────────────────────────────────────
        if self.create_shadow_lod:
            shadow_name = f"{base_name}_Shadow"
            try:
                shadow_obj = _duplicate_and_decimate(
                    context, source, shadow_name, SHADOW_LOD_RATIO,
                    triangulate=True,
                )
                # Remove armature modifiers — shadow meshes are not skinned
                for mod in list(shadow_obj.modifiers):
                    if mod.type == 'ARMATURE':
                        shadow_obj.modifiers.remove(mod)
                created.append(shadow_name)
            except Exception as exc:
                self.report({'WARNING'}, f"Could not create Shadow LOD: {exc}")

        # ── View LOD (optional) ─────────────────────────────────────────
        if self.create_view_lod:
            view_name = f"{base_name}_View"
            try:
                view_obj = _duplicate_and_decimate(
                    context, source, view_name, VIEW_LOD_RATIO,
                    triangulate=True,
                )
                # Remove armature modifiers — view meshes are not skinned
                for mod in list(view_obj.modifiers):
                    if mod.type == 'ARMATURE':
                        view_obj.modifiers.remove(mod)
                created.append(view_name)
            except Exception as exc:
                self.report({'WARNING'}, f"Could not create View LOD: {exc}")

        self.report({'INFO'}, f"Created {len(created)} LOD level(s): {', '.join(created)}")
        return {'FINISHED'}
