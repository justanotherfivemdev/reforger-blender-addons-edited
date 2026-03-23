import bpy
import re

from ..constants import CHARACTER_SKELETON_BONES, FACIAL_BONE_SET, WEIGHT_EPSILON, CHAR_TEMPLATE_PREFIX

# ---------------------------------------------------------------------------
# Re-use constants from the FBX exporter validators where available
# ---------------------------------------------------------------------------
try:
    from ...bk_fbx_exporter.validators import (
        COLLIDER_PREFIXES,
        VALID_LAYER_PRESETS,
        SPECIAL_PREFIXES,
        _check_lod_naming,
    )
except ImportError:
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
                   and not any(o.name.upper().startswith(p)
                               for p in COLLIDER_PREFIXES + SPECIAL_PREFIXES)]
        if lod_objects and non_lod:
            for obj in non_lod:
                issues.append(('WARNING',
                                f"'{obj.name}' has no _LOD suffix but other objects do"))
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
                    issues.append(('WARNING',
                                   f"'{base}' missing _LOD{i} (gap in LOD chain)"))
        return issues


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def _is_collider(obj):
    return any(obj.name.upper().startswith(p) for p in COLLIDER_PREFIXES)


def _check_armature(objects):
    """
    Exactly one armature should be present.
    Template armatures (CHAR_TEMPLATE_ prefix) are excluded from this check.
    """
    issues = []
    armatures = [o for o in objects
                 if o.type == 'ARMATURE' and not o.name.startswith(CHAR_TEMPLATE_PREFIX)]
    if not armatures:
        issues.append(('WARNING',
                       "No armature found — gear mesh will not animate correctly"))
    elif len(armatures) > 1:
        issues.append(('WARNING',
                       f"{len(armatures)} armatures found — expected exactly one"))
    return issues


def _check_facial_bone_skinning(objects):
    """
    ERROR if any render mesh has vertex groups that reference facial bones.

    Per the BI October 2024 skeleton update announcement:
    Equipment that uses old head-hierarchy (facial) bones 'will no longer be
    animated correctly'.  All facial-bone skinning must be migrated to the
    Head bone.  Use the 'Migrate Facial Weights to Head' operator.
    """
    issues = []
    for obj in objects:
        if (obj.type != 'MESH'
                or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        bad = [vg.name for vg in obj.vertex_groups if vg.name in FACIAL_BONE_SET]
        if bad:
            sample = ', '.join(bad[:3]) + ('...' if len(bad) > 3 else '')
            issues.append(('ERROR',
                           f"'{obj.name}' is skinned to {len(bad)} facial bone(s) "
                           f"({sample}) — facial-bone skinning breaks after the BI "
                           "Oct 2024 skeleton update. "
                           "Run 'Migrate Facial Weights to Head' to fix."))
    return issues


def _check_bone_match(objects):
    """
    All vertex groups on gear meshes should correspond to bones in the armature.

    If a CHAR_TEMPLATE_ armature is present in the scene it is used as the
    authoritative bone source (i.e. the actual BI skeleton), otherwise the
    first non-template armature is used.
    """
    issues = []

    # Prefer the template armature (actual BI skeleton) when available
    template_arm = next(
        (o for o in objects
         if o.type == 'ARMATURE' and o.name.startswith(CHAR_TEMPLATE_PREFIX)),
        None,
    )
    gear_arm = next(
        (o for o in objects
         if o.type == 'ARMATURE' and not o.name.startswith(CHAR_TEMPLATE_PREFIX)),
        None,
    )
    armature = template_arm or gear_arm
    if armature is None:
        return issues

    bone_names = {b.name for b in armature.data.bones}
    for obj in objects:
        if obj.type != 'MESH' or obj.name.startswith(CHAR_TEMPLATE_PREFIX):
            continue
        orphaned = [vg.name for vg in obj.vertex_groups if vg.name not in bone_names]
        if orphaned:
            issues.append(('WARNING',
                           f"'{obj.name}' has orphaned vertex group(s) with no matching "
                           f"bone: {', '.join(orphaned[:5])}"
                           + ('...' if len(orphaned) > 5 else '')))
    return issues


def _check_weight_coverage(objects):
    """Warn if any vertex has zero total weight (causes mesh distortion)."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or not obj.vertex_groups
                or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        zero_verts = [v.index for v in obj.data.vertices
                      if sum(g.weight for g in v.groups) < WEIGHT_EPSILON]
        if zero_verts:
            issues.append(('WARNING',
                           f"'{obj.name}' has {len(zero_verts)} unweighted vertex/vertices "
                           "(zero total weight) — these will not deform correctly"))
    return issues


def _check_max_influences(objects):
    """ERROR if any vertex has more than 4 bone influences (Enfusion engine limit)."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or not obj.vertex_groups
                or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        over = [v.index for v in obj.data.vertices if len(v.groups) > 4]
        if over:
            issues.append(('ERROR',
                           f"'{obj.name}' has {len(over)} vertex/vertices with >4 bone "
                           "influences — the Enfusion engine supports a maximum of 4. "
                           "Use 'Bind to Skeleton' to auto-limit influences."))
    return issues


def _check_modifier_stack(objects):
    """
    Rigged gear meshes must have an Armature modifier, and it must be the
    first modifier in the stack (Blender evaluates modifiers top-to-bottom).
    """
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or _is_collider(obj) or not obj.vertex_groups
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        arm_mods = [m for m in obj.modifiers if m.type == 'ARMATURE']
        if not arm_mods:
            issues.append(('WARNING',
                           f"'{obj.name}' has vertex groups but no Armature modifier — "
                           "add one and link it to the character armature"))
        elif obj.modifiers[0].type != 'ARMATURE':
            issues.append(('WARNING',
                           f"'{obj.name}': Armature modifier is not first in the stack — "
                           "move it to the top for correct deformation order"))
    return issues


def _check_lod_poly_counts(objects):
    """
    LOD meshes must have strictly decreasing face counts.
    LOD1 must have fewer faces than LOD0, etc.
    """
    issues = []
    lod_pattern = re.compile(r'^(.+?)_LOD(\d+)$', re.IGNORECASE)
    lod_groups: dict = {}
    for obj in objects:
        if obj.type != 'MESH' or obj.name.startswith(CHAR_TEMPLATE_PREFIX):
            continue
        m = lod_pattern.match(obj.name)
        if m:
            base, level = m.group(1), int(m.group(2))
            lod_groups.setdefault(base, {})[level] = obj

    for base, lods in lod_groups.items():
        sorted_levels = sorted(lods.keys())
        if len(sorted_levels) < 2:
            continue
        prev_count = len(lods[sorted_levels[0]].data.polygons)
        for level in sorted_levels[1:]:
            obj = lods[level]
            count = len(obj.data.polygons)
            prev_name = f"{base}_LOD{level - 1}"
            if count >= prev_count:
                issues.append(('WARNING',
                               f"'{obj.name}' has {count} face(s) but "
                               f"'{prev_name}' has {prev_count} — "
                               f"LOD{level} should have fewer faces than LOD{level - 1}"))
            prev_count = count

    return issues


def _check_gear_colliders(objects):
    """Gear colliders must have usage='Character' (BI Layer Preset requirement)."""
    issues = []
    for obj in objects:
        if not _is_collider(obj) or obj.name.startswith(CHAR_TEMPLATE_PREFIX):
            continue
        usage = obj.get("usage") or obj.get("layer_preset")
        if not usage:
            issues.append(('WARNING',
                           f"Collider '{obj.name}' has no 'usage' custom property — "
                           "set it to 'Character' for gear collision"))
        elif usage != 'Character':
            issues.append(('WARNING',
                           f"Collider '{obj.name}' has usage='{usage}' — "
                           "expected 'Character' for character gear"))
    return issues


def _check_uv_maps(objects):
    """Render meshes must have at least one UV map; colliders are exempt."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        if not obj.data.uv_layers:
            issues.append(('ERROR',
                           f"'{obj.name}' has no UV map — "
                           "gear meshes must have at least one UV channel for texturing"))
    return issues


def _check_scale(objects):
    """Warn if bounding box is unreasonably large (>3 m) or tiny (<0.01 m) for a gear item."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        dims = obj.dimensions
        max_dim = max(dims)
        pos_dims = [d for d in dims if d > 0]
        min_dim = min(pos_dims) if pos_dims else 0
        if max_dim > 3.0:
            issues.append(('WARNING',
                           f"'{obj.name}' bounding box is {max_dim:.2f} m — "
                           "unusually large for a gear item (expected ≤3 m)"))
        if max_dim > 0 and min_dim < 0.01:
            issues.append(('WARNING',
                           f"'{obj.name}' smallest dimension is {min_dim:.4f} m — "
                           "may be too small for gear (expected ≥0.01 m)"))
    return issues


def _check_scale_applied(objects):
    """Warn if any object has unapplied scale (non-unit values)."""
    issues = []
    for obj in objects:
        if (obj.type not in ('MESH', 'ARMATURE')
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        s = obj.scale
        if abs(s.x - 1.0) > 0.0001 or abs(s.y - 1.0) > 0.0001 or abs(s.z - 1.0) > 0.0001:
            issues.append(('WARNING',
                           f"'{obj.name}' has unapplied scale "
                           f"({s.x:.4f}, {s.y:.4f}, {s.z:.4f}) — "
                           "apply scale before export (Ctrl+A > Apply Scale)"))
    return issues


def _check_material_slots(objects):
    """Each render mesh should have at least one material assigned."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        if not obj.material_slots or all(ms.material is None for ms in obj.material_slots):
            issues.append(('WARNING',
                           f"'{obj.name}' has no material assigned — "
                           "gear meshes require at least one material for Workbench texturing"))
    return issues


def _check_triangulation(objects):
    """INFO if N-gons are present (BI recommends triangulated geometry for export)."""
    issues = []
    for obj in objects:
        if (obj.type != 'MESH' or _is_collider(obj)
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        ngons = [p for p in obj.data.polygons if len(p.vertices) > 4]
        if ngons:
            issues.append(('INFO',
                           f"'{obj.name}' has {len(ngons)} N-gon(s) — "
                           "triangulate before export for best Enfusion compatibility "
                           "(Object > Triangulate Faces or add a Triangulate modifier)"))
    return issues


def _check_name_convention(objects):
    """Warn if object names contain characters outside letters, digits, and underscores."""
    bad_chars = re.compile(r'[^A-Za-z0-9_]')
    issues = []
    for obj in objects:
        if (obj.type not in ('MESH', 'ARMATURE')
                or obj.name.startswith(CHAR_TEMPLATE_PREFIX)):
            continue
        if bad_chars.search(obj.name):
            issues.append(('WARNING',
                           f"'{obj.name}' contains non-standard characters — "
                           "BI naming should use only letters, digits, and underscores"))
    return issues


# ---------------------------------------------------------------------------
# Master validation function
# ---------------------------------------------------------------------------

def validate_gear_objects(objects):
    """
    Run all gear-specific validation checks aligned with Bohemia Interactive's
    2024 standards (including the October 2024 220-bone skeleton update).

    Returns a list of (severity, message) tuples.
    severity is one of: 'ERROR', 'WARNING', 'INFO'
    """
    issues = []

    # ── BI Oct 2024 skeleton update — critical checks ────────────────────────
    issues.extend(_check_armature(objects))
    issues.extend(_check_facial_bone_skinning(objects))   # new v220

    # ── Rigging / weight checks ──────────────────────────────────────────────
    issues.extend(_check_bone_match(objects))
    issues.extend(_check_weight_coverage(objects))
    issues.extend(_check_max_influences(objects))         # ERROR (hard engine limit)
    issues.extend(_check_modifier_stack(objects))

    # ── LOD chain integrity ──────────────────────────────────────────────────
    issues.extend(_check_lod_naming(objects))
    issues.extend(_check_lod_poly_counts(objects))

    # ── Collider / layer-preset ──────────────────────────────────────────────
    issues.extend(_check_gear_colliders(objects))

    # ── Mesh quality / export readiness ─────────────────────────────────────
    issues.extend(_check_uv_maps(objects))
    issues.extend(_check_scale(objects))
    issues.extend(_check_scale_applied(objects))
    issues.extend(_check_material_slots(objects))
    issues.extend(_check_triangulation(objects))          # INFO
    issues.extend(_check_name_convention(objects))

    return issues


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

class CHARGEAR_OT_validate_gear(bpy.types.Operator):
    """Run BI-standard gear validation checks and report results"""
    bl_idname = "chargear.validate_gear"
    bl_label = "Validate Gear"
    bl_options = {'REGISTER'}

    def execute(self, context):
        objects = list(context.scene.objects)   # scene-scoped, not all bpy.data.objects
        issues = validate_gear_objects(objects)

        if not issues:
            self.report({'INFO'}, "Gear validation passed — no issues found")
            return {'FINISHED'}

        error_count   = sum(1 for sev, _ in issues if sev == 'ERROR')
        warning_count = sum(1 for sev, _ in issues if sev == 'WARNING')
        info_count    = sum(1 for sev, _ in issues if sev == 'INFO')

        for severity, message in issues:
            self.report({severity}, message)

        self.report({'INFO'},
                    f"Validation complete: {error_count} error(s), "
                    f"{warning_count} warning(s), {info_count} info")
        return {'FINISHED'}
