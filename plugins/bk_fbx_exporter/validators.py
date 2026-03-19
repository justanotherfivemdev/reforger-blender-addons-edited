import bpy
import re

# Valid Arma Reforger collider prefixes
COLLIDER_PREFIXES = ('UBX_', 'UCX_', 'UTM_', 'USP_', 'UCS_', 'UCL_')

# Valid Arma Reforger Layer Presets
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

# Special object prefixes
SPECIAL_PREFIXES = ('COM_', 'OCC_', 'LC_', 'PRT_', 'BOXVOL_', 'SPHVOL_', 'SOCKET_')


def validate_export_objects(objects):
    """Run all validation checks on objects to be exported.
    Returns list of (severity, message) tuples. severity: 'ERROR', 'WARNING', 'INFO'
    """
    issues = []
    issues.extend(_check_duplicate_names(objects))
    issues.extend(_check_lod_naming(objects))
    issues.extend(_check_collider_prefixes(objects))
    issues.extend(_check_layer_presets(objects))
    issues.extend(_check_land_contacts(objects))
    return issues


def _check_duplicate_names(objects):
    """Warn about Blender .001 suffixes that get stripped on Enfusion import."""
    issues = []
    pattern = re.compile(r'\.\d{3}$')
    for obj in objects:
        if pattern.search(obj.name):
            issues.append(('WARNING', f"'{obj.name}' has Blender duplicate suffix -- will be stripped on import, may cause name collision"))
    return issues


def _check_lod_naming(objects):
    """Check LOD naming conventions."""
    issues = []
    mesh_objects = [o for o in objects if o.type == 'MESH']
    lod_pattern = re.compile(r'_LOD(\d+)$', re.IGNORECASE)

    lod_objects = [o for o in mesh_objects if lod_pattern.search(o.name)]
    non_lod_meshes = [o for o in mesh_objects
                      if not lod_pattern.search(o.name)
                      and not any(o.name.startswith(p) for p in COLLIDER_PREFIXES + SPECIAL_PREFIXES)]

    if lod_objects and non_lod_meshes:
        for obj in non_lod_meshes:
            issues.append(('WARNING', f"'{obj.name}' has no _LOD suffix but other objects do"))

    # Check for case mismatch
    for obj in lod_objects:
        match = lod_pattern.search(obj.name)
        if match and '_lod' in obj.name.lower() and '_LOD' not in obj.name:
            issues.append(('WARNING', f"'{obj.name}' uses lowercase _lod -- Enfusion expects _LOD (uppercase)"))

    # Check for LOD gaps
    lod_bases = {}
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


def _check_collider_prefixes(objects):
    """Validate collider naming."""
    issues = []
    for obj in objects:
        if obj.type != 'MESH':
            continue
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in COLLIDER_PREFIXES)
        if not is_collider:
            continue
        # Check vertex count
        if len(obj.data.vertices) > 65535:
            issues.append(('ERROR', f"Collider '{obj.name}' has {len(obj.data.vertices)} vertices (max 65535)"))
    return issues


def _check_layer_presets(objects):
    """Check that colliders have valid Layer Preset custom properties."""
    issues = []
    for obj in objects:
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in COLLIDER_PREFIXES)
        if not is_collider:
            continue

        usage = obj.get("usage") or obj.get("layer_preset")
        if not usage:
            issues.append(('WARNING', f"Collider '{obj.name}' has no 'usage' custom property (Layer Preset required for Enfusion)"))
        elif usage not in VALID_LAYER_PRESETS:
            issues.append(('WARNING', f"Collider '{obj.name}' has unknown Layer Preset '{usage}' -- may not be recognized by Enfusion"))
    return issues


def _check_land_contacts(objects):
    """Check LC_ land contact points (minimum 2 required for ground snapping)."""
    issues = []
    lc_count = sum(1 for o in objects if o.name.upper().startswith('LC_'))
    if lc_count == 1:
        issues.append(('WARNING', "Only 1 LC_ land contact found -- minimum 2 required for ground snapping"))
    return issues
