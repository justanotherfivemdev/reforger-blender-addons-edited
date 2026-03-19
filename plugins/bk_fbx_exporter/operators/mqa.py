import bpy
import bmesh
import re
from mathutils import Vector

_COLLIDER_PREFIXES = ('UBX_', 'UCX_', 'UTM_', 'USP_', 'UCS_', 'UCL_')
_SPECIAL_PREFIXES = ('COM_', 'OCC_', 'LC_', 'PRT_', 'BOXVOL_', 'SPHVOL_', 'SOCKET_')

_VALID_LAYER_PRESETS = {
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

# Thresholds
_SHORT_EDGE_THRESHOLD = 0.0001  # meters
_SMALL_FACE_THRESHOLD = 0.00001  # sq meters
_UV_RANGE = (-32.0, 32.0)


class AREXPORT_OT_run_mqa(bpy.types.Operator):
    bl_idname = "arexport.run_mqa"
    bl_label = "Model Quality Assurance"
    bl_description = "Run Enfusion MQA checks on selected objects and highlight issues"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bool(context.selected_objects)

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        issues = []

        for obj in objects:
            issues.extend(self._check_naming(obj))
            issues.extend(self._check_collider(obj))
            issues.extend(self._check_mesh_quality(obj))
            issues.extend(self._check_uvs(obj))

        if not issues:
            self.report({'INFO'}, f"MQA passed: {len(objects)} object(s) checked, no issues found")
            return {'FINISHED'}

        # Report issues
        errors = [msg for sev, msg in issues if sev == 'ERROR']
        warnings = [msg for sev, msg in issues if sev == 'WARNING']

        for msg in errors:
            self.report({'ERROR'}, msg)
        for msg in warnings:
            self.report({'WARNING'}, msg)

        self.report({'INFO'}, f"MQA: {len(errors)} error(s), {len(warnings)} warning(s) across {len(objects)} object(s)")
        return {'FINISHED'}

    def _check_naming(self, obj):
        issues = []
        # Blender duplicate suffix
        if re.search(r'\.\d{3}$', obj.name):
            issues.append(('WARNING', f"'{obj.name}': Blender duplicate suffix (.00x) will be stripped on Enfusion import"))

        # Check valid prefix/suffix
        name_upper = obj.name.upper()
        has_known_prefix = any(name_upper.startswith(p) for p in _COLLIDER_PREFIXES + _SPECIAL_PREFIXES)
        has_lod_suffix = bool(re.search(r'_LOD\d+$', name_upper))

        if not has_known_prefix and not has_lod_suffix:
            # Not a recognized Enfusion object -- just info
            pass

        return issues

    def _check_collider(self, obj):
        issues = []
        name_upper = obj.name.upper()
        is_collider = any(name_upper.startswith(p) for p in _COLLIDER_PREFIXES)
        if not is_collider:
            return issues

        # Vertex count
        vert_count = len(obj.data.vertices)
        if vert_count > 65535:
            issues.append(('ERROR', f"'{obj.name}': {vert_count} vertices exceeds 65535 limit"))

        # Layer preset
        usage = obj.get("usage") or obj.get("layer_preset")
        if not usage:
            issues.append(('WARNING', f"'{obj.name}': Missing 'usage' custom property (Layer Preset required)"))
        elif usage not in _VALID_LAYER_PRESETS:
            issues.append(('WARNING', f"'{obj.name}': Unknown Layer Preset '{usage}'"))

        # UCX convexity check
        if name_upper.startswith('UCX_'):
            issues.extend(self._check_convexity(obj))

        # Origin check for UCL/UCS/USP (must be at geometry center)
        if any(name_upper.startswith(p) for p in ('UCL_', 'UCS_', 'USP_')):
            bbox_center = Vector((0, 0, 0))
            for corner in obj.bound_box:
                bbox_center += Vector(corner)
            bbox_center /= 8.0
            if bbox_center.length > 0.01:
                issues.append(('WARNING', f"'{obj.name}': Origin not at geometry center (offset: {bbox_center.length:.3f}m). Use Set Origin > Origin to Geometry"))

        return issues

    def _check_convexity(self, obj):
        issues = []
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Non-manifold edges
        non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
        if non_manifold > 0:
            issues.append(('WARNING', f"'{obj.name}': UCX has {non_manifold} non-manifold edge(s)"))

        # Non-planar faces (ngons with significant non-planarity)
        for face in bm.faces:
            if len(face.verts) > 3:
                normal = face.normal
                center = face.calc_center_median()
                for vert in face.verts:
                    dist = abs((vert.co - center).dot(normal))
                    if dist > 0.001:
                        issues.append(('WARNING', f"'{obj.name}': UCX has non-planar face(s)"))
                        break
                else:
                    continue
                break

        bm.free()
        return issues

    def _check_mesh_quality(self, obj):
        issues = []
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        # Short edges
        short_edges = sum(1 for e in bm.edges if e.calc_length() < _SHORT_EDGE_THRESHOLD)
        if short_edges > 0:
            issues.append(('WARNING', f"'{obj.name}': {short_edges} short edge(s) (< {_SHORT_EDGE_THRESHOLD}m)"))

        # Small faces
        small_faces = sum(1 for f in bm.faces if f.calc_area() < _SMALL_FACE_THRESHOLD)
        if small_faces > 0:
            issues.append(('WARNING', f"'{obj.name}': {small_faces} small face(s) (< {_SMALL_FACE_THRESHOLD} sq m)"))

        bm.free()
        return issues

    def _check_uvs(self, obj):
        issues = []
        if not obj.data.uv_layers:
            # Colliders don't need UVs
            if not any(obj.name.upper().startswith(p) for p in _COLLIDER_PREFIXES):
                issues.append(('WARNING', f"'{obj.name}': No UV map"))
            return issues

        uv_layer = obj.data.uv_layers.active
        if uv_layer is None:
            return issues

        out_of_range = 0
        for loop in obj.data.loops:
            uv = uv_layer.data[loop.index].uv
            if uv[0] < _UV_RANGE[0] or uv[0] > _UV_RANGE[1] or uv[1] < _UV_RANGE[0] or uv[1] > _UV_RANGE[1]:
                out_of_range += 1
                break  # one warning per object is enough

        if out_of_range:
            issues.append(('WARNING', f"'{obj.name}': UV coordinates outside valid range ({_UV_RANGE[0]} to {_UV_RANGE[1]})"))

        return issues


class AREXPORT_OT_batch_export_collections(bpy.types.Operator):
    bl_idname = "arexport.batch_export_collections"
    bl_label = "Batch Export Collections"
    bl_description = "Export each top-level collection as a separate FBX file"
    bl_options = {'REGISTER'}

    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Directory to export FBX files to",
        subtype='DIR_PATH',
        default="//"
    )
    only_visible: bpy.props.BoolProperty(
        name="Only Visible",
        description="Only export visible collections",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return bool(bpy.data.collections)

    def execute(self, context):
        import os

        export_dir = bpy.path.abspath(self.export_path)
        if not os.path.isdir(export_dir):
            try:
                os.makedirs(export_dir)
            except OSError as e:
                self.report({'ERROR'}, f"Cannot create directory: {e}")
                return {'CANCELLED'}

        exported = 0
        for col in context.scene.collection.children:
            if self.only_visible:
                layer_col = self._find_layer_collection(context.view_layer.layer_collection, col.name)
                if layer_col and layer_col.hide_viewport:
                    continue

            if not col.objects:
                continue

            filepath = os.path.join(export_dir, f"{col.name}.fbx")

            # Select only objects in this collection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in col.all_objects:
                obj.select_set(True)

            if not context.selected_objects:
                continue

            context.view_layer.objects.active = context.selected_objects[0]

            bpy.ops.export_scene.fbx(
                filepath=filepath,
                use_selection=True,
                apply_scale_options='FBX_SCALE_ALL',
                object_types={'MESH', 'EMPTY', 'ARMATURE'},
                use_custom_props=True,
                add_leaf_bones=False,
                bake_anim=False,
            )
            exported += 1

        bpy.ops.object.select_all(action='DESELECT')
        self.report({'INFO'}, f"Exported {exported} collection(s) to {export_dir}")
        return {'FINISHED'}

    def _find_layer_collection(self, layer_col, name):
        if layer_col.name == name:
            return layer_col
        for child in layer_col.children:
            result = self._find_layer_collection(child, name)
            if result:
                return result
        return None

    def invoke(self, context, event):
        self.export_path = getattr(context.scene, 'ar_export_path', '//')
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_path")
        layout.prop(self, "only_visible")


classes = (
    AREXPORT_OT_run_mqa,
    AREXPORT_OT_batch_export_collections,
)
