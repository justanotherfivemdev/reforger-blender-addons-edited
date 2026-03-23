import bpy
import re

from ..constants import CHARACTER_SKELETON_BONES

# Re-use constants from the existing FBX exporter validators where available
try:
    from ...bk_fbx_exporter.validators import (
        COLLIDER_PREFIXES,
        VALID_LAYER_PRESETS,
        SPECIAL_PREFIXES,
        _check_lod_naming,
    )
except ImportError:
    # Fallback definitions if the exporter module is not loaded
    COLLIDER_PREFIXES = ('UBX_', 'UCX_', 'UTM_', 'USP_', 'UCS_', 'UCL_')
    VALID_LAYER_PRESETS = {
        'Building', 'BuildingFire', 'BuildingFireView',
        'Prop', 'PropView', 'PropFireView',
        'FireGeo', 'FireView',
        'Vehicle', 'VehicleFire', 'VehicleFireView',
        'ItemFireView',
        'Door', 'DoorFireView',
        'Tree', 'TreeFireView',
        'Wheel', 'Glass', 'GlassFire',
        'Ladder', 'Character', 'CharacterAI', 'Terrain',
    }
    SPECIAL_PREFIXES = ('COM_', 'OCC_', 'LC_', 'PRT_', 'BOXVOL_', 'SPHVOL_', 'SOCKET_')

    def _check_lod_naming(objects):
        issues = []
        mesh_objects = [o for o in objects if o.type == 'MESH']
        lod_pattern = re.compile(r'_LOD(\d+)$', re.IGNORECASE)
        lod_objects = [o for o in mesh_objects if lod_pattern.search(o.name)]
        non_lod = [o for o in mesh_objects
                   if not lod_pattern.search(o.name)
                   and not any(o.name.upper().startswith(p) for p in COLLIDER_PREFIXES + SPECIAL_PREFIXES)]
        if lod_objects and non_lod:
            for obj in non_lod:
                issues.append(('WARNING', f"'{obj.name}' has no _LOD suffix but other objects do"))
        lod_bases: dict = {}
        for obj in lod_objects:
            match = lod_pattern.search(obj.name)
            if match:
                base = obj.name[:match.start()]
                level = int(match.group(1))
                lod_bases.setdefault(base, set()).add(level)
        for base, levels in lod_bases.items():
            max_level = max(levels)
            for i in range(max_level + 1):
                if i not in levels:
                    issues.append(('WARNING', f"'{base}' missing _LOD{i} (gap in LOD chain)"))
        return issues


def _check_armature(objects):
    """Exactly one armature should be present."""
    issues = []
    armatures = [o for o in objects if o.type == 'ARMATURE']
    if not armatures:
        issues.append(('WARNING', "No armature found — gear mesh will not animate correctly"))
    elif len(armatures) > 1:
        issues.append(('WARNING', f"{len(armatures)} armatures found — expected exactly 1"))
    return issues


def _check_bone_match(objects):
    """All vertex groups on gear meshes should correspond to bones in the armature."""
    issues = []
    armature = next((o for o in objects if o.type == 'ARMATURE'), None)
    if armature is None:
        return issues
    bone_names = {b.name for b in armature.data.bones}
    for obj in objects:
        if obj.type != 'MESH':
            continue
        for vg in obj.vertex_groups:
            if vg.name not in bone_names:
                issues.append(('WARNING', f"'{obj.name}' has orphaned vertex group '{vg.name}' (no matching bone)"))
    return issues


def _check_weight_coverage(objects):
    """Warn if any vertex has zero total weight (unweighted vertices cause mesh distortion)."""
    issues = []
    for obj in objects:
        if obj.type != 'MESH' or not obj.vertex_groups:
            continue
        zero_weight_verts = []
        for v in obj.data.vertices:
            total = sum(g.weight for g in v.groups)
            if total < 1e-6:
                zero_weight_verts.append(v.index)
        if zero_weight_verts:
            issues.append(('WARNING',
                           f"'{obj.name}' has {len(zero_weight_verts)} unweighted vertex/vertices (zero total weight)"))
    return issues


def _check_max_influences(objects):
    """Warn if any vertex has more than 4 bone influences (Enfusion limit)."""
    issues = []
    for obj in objects:
        if obj.type != 'MESH' or not obj.vertex_groups:
            continue
        over_limit = []
        for v in obj.data.vertices:
            if len(v.groups) > 4:
                over_limit.append(v.index)
        if over_limit:
            issues.append(('WARNING',
                           f"'{obj.name}' has {len(over_limit)} vertex/vertices with >4 bone influences (Enfusion limit)"))
    return issues


def _check_gear_colliders(objects):
    """Gear colliders must have usage='Character'."""
    issues = []
    for obj in objects:
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in COLLIDER_PREFIXES)
        if not is_collider:
            continue
        usage = obj.get("usage") or obj.get("layer_preset")
        if not usage:
            issues.append(('WARNING', f"Collider '{obj.name}' has no 'usage' property — should be 'Character' for gear"))
        elif usage != 'Character':
            issues.append(('WARNING', f"Collider '{obj.name}' has usage='{usage}' — expected 'Character' for gear"))
    return issues


def _check_uv_maps(objects):
    """Gear render meshes must have at least one UV map; colliders are exempt."""
    issues = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in COLLIDER_PREFIXES)
        if is_collider:
            continue
        if not obj.data.uv_layers:
            issues.append(('ERROR', f"'{obj.name}' has no UV map — gear meshes must have at least one UV map"))
    return issues


def _check_scale(objects):
    """Warn if the mesh bounding box is unreasonably large (>3 m) or tiny (<0.01 m) for gear."""
    issues = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in COLLIDER_PREFIXES)
        if is_collider:
            continue
        dims = obj.dimensions
        max_dim = max(dims)
        min_dim = min(d for d in dims if d > 0) if any(d > 0 for d in dims) else 0
        if max_dim > 3.0:
            issues.append(('WARNING',
                           f"'{obj.name}' bounding box is {max_dim:.2f} m wide — unusually large for a gear item (>3 m)"))
        if max_dim > 0 and min_dim < 0.01:
            issues.append(('WARNING',
                           f"'{obj.name}' smallest dimension is {min_dim:.4f} m — may be too small for gear (<0.01 m)"))
    return issues


def validate_gear_objects(objects):
    """Run all gear-specific validation checks.
    Returns a list of (severity, message) tuples; severity is 'ERROR', 'WARNING', or 'INFO'.
    """
    issues = []
    issues.extend(_check_armature(objects))
    issues.extend(_check_bone_match(objects))
    issues.extend(_check_weight_coverage(objects))
    issues.extend(_check_max_influences(objects))
    issues.extend(_check_lod_naming(objects))
    issues.extend(_check_gear_colliders(objects))
    issues.extend(_check_uv_maps(objects))
    issues.extend(_check_scale(objects))
    return issues


class CHARGEAR_OT_validate_gear(bpy.types.Operator):
    """Run gear-specific validation checks and report results"""
    bl_idname = "chargear.validate_gear"
    bl_label = "Validate Gear"
    bl_options = {'REGISTER'}

    def execute(self, context):
        objects = list(bpy.data.objects)
        issues = validate_gear_objects(objects)

        if not issues:
            self.report({'INFO'}, "Gear validation passed — no issues found")
            return {'FINISHED'}

        error_count = sum(1 for sev, _ in issues if sev == 'ERROR')
        warning_count = sum(1 for sev, _ in issues if sev == 'WARNING')

        for severity, message in issues:
            self.report({severity}, message)

        summary = f"Validation complete: {error_count} error(s), {warning_count} warning(s)"
        self.report({'INFO'}, summary)

        return {'FINISHED'}
