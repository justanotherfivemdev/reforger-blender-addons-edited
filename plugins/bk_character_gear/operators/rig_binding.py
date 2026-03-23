import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty

from ..constants import GEAR_TYPE_ITEMS, GEAR_BONE_MAPPING, FACIAL_BONE_SET, WEIGHT_EPSILON


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_or_add_armature_modifier(mesh_obj, armature):
    """Return the first existing Armature modifier on *mesh_obj*, or create one."""
    for mod in mesh_obj.modifiers:
        if mod.type == 'ARMATURE':
            mod.object = armature
            return mod
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = armature
    return mod


def _normalize_and_limit(context, mesh_obj):
    """
    Normalize all vertex-group weights and limit to 4 bone influences per
    vertex (the Enfusion engine hard limit).  Cleans up near-zero entries.
    """
    prev_active = context.view_layer.objects.active
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    context.view_layer.objects.active = mesh_obj

    if mesh_obj.vertex_groups:
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
        bpy.ops.object.vertex_group_normalize_all(lock_active=False)
        bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.0001,
                                          keep_single=True)

    context.view_layer.objects.active = prev_active


def _apply_restricted_auto_weights(context, mesh_obj, armature, relevant_bones):
    """
    Apply heat-diffuse automatic weights to *mesh_obj* using Blender's
    ARMATURE_AUTO, then restrict the result to *relevant_bones* only.

    Pipeline:
      1. ARMATURE_AUTO - heat-diffuse weights for ALL armature bones
      2. Remove vertex groups for bones NOT in relevant_bones
      3. Normalize remaining weights
      4. Limit to 4 influences per vertex  (Enfusion engine requirement)
      5. Final normalize + clean near-zero entries

    Falls back to ARMATURE_ENVELOPE weighting if heat diffuse fails
    (e.g. mesh has no interior volume for heat diffusion).

    Returns (success: bool, message: str).
    """
    armature_bone_names = {b.name for b in armature.data.bones}
    valid_bones = [b for b in relevant_bones if b in armature_bone_names]

    if not valid_bones:
        return False, "None of the expected bones are present in the armature"

    # Step 1: apply heat-diffuse (ARMATURE_AUTO) via parent_set
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    armature.select_set(True)
    context.view_layer.objects.active = armature

    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except Exception:
        # Fallback: envelope-based weighting (works on flat / open meshes)
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        armature.select_set(True)
        context.view_layer.objects.active = armature
        try:
            bpy.ops.object.parent_set(type='ARMATURE_ENVELOPE')
        except Exception as exc:
            return False, f"Auto-weight failed (heat + envelope): {exc}"

    # Step 2: remove vertex groups for bones outside relevant_bones
    relevant_set = set(valid_bones)
    to_remove = [vg for vg in mesh_obj.vertex_groups if vg.name not in relevant_set]
    for vg in to_remove:
        mesh_obj.vertex_groups.remove(vg)

    # Steps 3-5: normalize, limit, clean
    _normalize_and_limit(context, mesh_obj)

    return True, f"Applied restricted auto-weights to {len(valid_bones)} bone(s)"


# ---------------------------------------------------------------------------
# Operator: Bind to Skeleton
# ---------------------------------------------------------------------------

class CHARGEAR_OT_bind_to_skeleton(bpy.types.Operator):
    """Bind the selected gear mesh to the character skeleton with automatic weight painting"""
    bl_idname = "chargear.bind_to_skeleton"
    bl_label = "Bind to Skeleton"
    bl_options = {'REGISTER', 'UNDO'}

    gear_type: EnumProperty(
        name="Gear Type",
        items=GEAR_TYPE_ITEMS,
        default='HEADGEAR',
    )

    def execute(self, context):
        armature = next((o for o in context.scene.objects if o.type == 'ARMATURE'), None)
        if not armature:
            self.report({'ERROR'},
                        "No armature found in the scene. "
                        "Import or link the character armature first.")
            return {'CANCELLED'}

        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        relevant_bones = GEAR_BONE_MAPPING.get(self.gear_type, [])
        armature_bone_names = {b.name for b in armature.data.bones}

        bound = 0
        for mesh_obj in mesh_objects:

            if self.gear_type == 'HEADGEAR':
                # Rigid bind: all vertices to Head at weight 1.0
                # Per BI Oct 2024: NEVER use facial bones for headgear.
                # Chin straps must also use Head as the safe anchor bone.
                _get_or_add_armature_modifier(mesh_obj, armature)
                head_bone = "Head"
                if head_bone not in armature_bone_names:
                    self.report({'WARNING'},
                                "Armature has no 'Head' bone — rigid bind skipped.")
                    continue
                if head_bone not in mesh_obj.vertex_groups:
                    mesh_obj.vertex_groups.new(name=head_bone)
                vg = mesh_obj.vertex_groups[head_bone]
                all_verts = [v.index for v in mesh_obj.data.vertices]
                vg.add(all_verts, 1.0, 'REPLACE')
                # Remove any stray facial-bone vertex groups
                for stray_name in [v.name for v in mesh_obj.vertex_groups
                                   if v.name in FACIAL_BONE_SET]:
                    mesh_obj.vertex_groups.remove(mesh_obj.vertex_groups[stray_name])
                _normalize_and_limit(context, mesh_obj)

            elif self.gear_type == 'ACCESSORY':
                # Bind to first matching bone
                _get_or_add_armature_modifier(mesh_obj, armature)
                valid = [b for b in relevant_bones if b in armature_bone_names]
                if valid:
                    bone_name = valid[0]
                    if bone_name not in mesh_obj.vertex_groups:
                        mesh_obj.vertex_groups.new(name=bone_name)
                    vg = mesh_obj.vertex_groups[bone_name]
                    all_verts = [v.index for v in mesh_obj.data.vertices]
                    vg.add(all_verts, 1.0, 'REPLACE')
                    _normalize_and_limit(context, mesh_obj)
                else:
                    self.report({'WARNING'},
                                f"'{mesh_obj.name}': no relevant accessory bone found "
                                "— select the target bone manually in Weight Paint mode.")

            else:
                # Deforming gear (vest, pants, boots, gloves, backpack, full body)
                # Uses heat-diffuse weights restricted to gear-relevant bones.
                success, msg = _apply_restricted_auto_weights(
                    context, mesh_obj, armature, relevant_bones)
                if not success:
                    self.report({'WARNING'}, f"'{mesh_obj.name}': {msg}")
                    continue

            # Warn about orphaned vertex groups
            orphaned = [vg.name for vg in mesh_obj.vertex_groups
                        if vg.name not in armature_bone_names]
            if orphaned:
                self.report({'WARNING'},
                            f"'{mesh_obj.name}' has orphaned vertex groups "
                            f"with no matching bone: {', '.join(orphaned)}")

            bound += 1

        self.report({'INFO'},
                    f"Bound {bound} mesh(es) to skeleton using '{self.gear_type}' mode")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Operator: Transfer Weights from Reference Mesh
# ---------------------------------------------------------------------------

class CHARGEAR_OT_transfer_weights(bpy.types.Operator):
    """Transfer weights from a reference mesh to the selected gear mesh(es) using Data Transfer"""
    bl_idname = "chargear.transfer_weights"
    bl_label = "Transfer Weights"
    bl_options = {'REGISTER', 'UNDO'}

    source_object: StringProperty(
        name="Source Object",
        description="Name of the reference mesh to transfer weights from "
                    "(e.g. the official character body mesh)",
        default="",
    )

    def execute(self, context):
        if not self.source_object:
            self.report({'ERROR'}, "No source object specified")
            return {'CANCELLED'}

        source = bpy.data.objects.get(self.source_object)
        if source is None or source.type != 'MESH':
            self.report({'ERROR'},
                        f"Source object '{self.source_object}' not found or is not a mesh")
            return {'CANCELLED'}

        targets = [o for o in context.selected_objects
                   if o.type == 'MESH' and o != source]
        if not targets:
            self.report({'ERROR'}, "No target mesh objects selected")
            return {'CANCELLED'}

        transferred = 0
        for target in targets:
            mod = target.modifiers.new(name="DataTransfer_Weights", type='DATA_TRANSFER')
            mod.object = source
            mod.use_vert_data = True
            mod.data_types_verts = {'VGROUP_WEIGHTS'}
            mod.vert_mapping = 'NEAREST'

            context.view_layer.objects.active = target
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
                _normalize_and_limit(context, target)
                transferred += 1
            except Exception as exc:
                self.report({'WARNING'},
                            f"Could not apply weight transfer to '{target.name}': {exc}")
                target.modifiers.remove(mod)

        self.report({'INFO'},
                    f"Transferred weights to {transferred} object(s) from '{self.source_object}'")
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Operator: Migrate Facial Weights to Head bone (BI Oct 2024 skeleton update)
# ---------------------------------------------------------------------------

class CHARGEAR_OT_migrate_facial_weights(bpy.types.Operator):
    """
    Scan all gear meshes in the scene for vertex groups that reference facial
    bones and merge their weights into the Head bone.

    Implements the official BI recommendation from the October 2024 skeleton
    update: 'If an asset is rigged to specific facial bones (e.g. a chin strap
    on a helmet) it may require re-skinning. The chin strap can be skinned to
    the Head bone as a temporary solution.'
    """
    bl_idname = "chargear.migrate_facial_weights"
    bl_label = "Migrate Facial Weights to Head"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        migrated_objects = []

        for obj in context.scene.objects:
            if obj.type != 'MESH':
                continue

            facial_vgs = [vg for vg in obj.vertex_groups if vg.name in FACIAL_BONE_SET]
            if not facial_vgs:
                continue

            facial_names = {vg.name for vg in facial_vgs}

            # Ensure Head vertex group exists
            if "Head" not in obj.vertex_groups:
                obj.vertex_groups.new(name="Head")
            head_vg = obj.vertex_groups["Head"]

            # Accumulate facial bone weights into Head per vertex
            for vert in obj.data.vertices:
                facial_total = sum(
                    g.weight for g in vert.groups
                    if obj.vertex_groups[g.group].name in facial_names
                )
                if facial_total < WEIGHT_EPSILON:
                    continue
                existing_head = next(
                    (g.weight for g in vert.groups
                     if obj.vertex_groups[g.group].name == "Head"),
                    0.0,
                )
                head_vg.add([vert.index],
                            min(existing_head + facial_total, 1.0),
                            'REPLACE')

            # Remove facial-bone vertex groups
            for vg in facial_vgs:
                obj.vertex_groups.remove(vg)

            _normalize_and_limit(context, obj)
            migrated_objects.append(f"{obj.name} ({len(facial_vgs)} VG(s))")

        if migrated_objects:
            self.report({'INFO'},
                        "Migrated facial weights to Head on: "
                        + ", ".join(migrated_objects))
        else:
            self.report({'INFO'},
                        "No facial-bone vertex groups found — nothing to migrate")

        return {'FINISHED'}
