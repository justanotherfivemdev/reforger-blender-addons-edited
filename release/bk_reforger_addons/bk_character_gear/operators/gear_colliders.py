import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty

# Layer preset items for colliders.  "Character" is for general gear collision,
# "FireGeo" is for armored gear that must stop bullets (per BI vest docs).
_COLLIDER_LAYER_ITEMS = [
    ('Character', "Character", "Standard character collision layer"),
    ('FireGeo',   "FireGeo",   "Ballistic protection layer — stops projectiles (armored vests, plates)"),
]


class CHARGEAR_OT_create_gear_collider(bpy.types.Operator):
    """Generate a UTM_ trimesh collider from the selected gear mesh"""
    bl_idname = "chargear.create_gear_collider"
    bl_label = "Create Gear Collider"
    bl_options = {'REGISTER', 'UNDO'}

    layer_preset: EnumProperty(
        name="Layer Preset",
        description="Enfusion layer preset for this collider",
        items=_COLLIDER_LAYER_ITEMS,
        default='Character',
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        source = mesh_objects[0]

        # Determine base name (strip _LOD0 if present)
        base_name = source.name
        if base_name.upper().endswith("_LOD0"):
            base_name = base_name[:-5]

        collider_name = f"UTM_{base_name}"

        # Duplicate the mesh
        new_data = source.data.copy()
        collider_obj = source.copy()
        collider_obj.data = new_data
        collider_obj.name = collider_name
        collider_obj.data.name = collider_name

        for col in source.users_collection:
            col.objects.link(collider_obj)

        # Remove any armature modifiers — colliders should not be skinned
        for mod in list(collider_obj.modifiers):
            if mod.type == 'ARMATURE':
                collider_obj.modifiers.remove(mod)

        # Apply heavy decimation (~5% of original)
        dec_mod = collider_obj.modifiers.new(name="Decimate", type='DECIMATE')
        dec_mod.ratio = 0.05
        dec_mod.use_collapse_triangulate = True

        context.view_layer.objects.active = collider_obj
        try:
            bpy.ops.object.modifier_apply(modifier=dec_mod.name)
        except Exception as exc:
            self.report({'WARNING'}, f"Could not apply decimate to collider: {exc}")
            collider_obj.modifiers.remove(dec_mod)

        # Set layer preset property (Character or FireGeo for armored gear)
        collider_obj["usage"] = self.layer_preset

        # Wire display so it is visually distinct
        collider_obj.display_type = 'WIRE'

        self.report({'INFO'},
                    f"Created collider '{collider_name}' with usage='{self.layer_preset}'")
        return {'FINISHED'}


class CHARGEAR_OT_create_primitive_collider(bpy.types.Operator):
    """Create a bounding-box primitive collider (UBX_) fitted to the selected gear mesh"""
    bl_idname = "chargear.create_primitive_collider"
    bl_label = "Create Primitive Collider"
    bl_options = {'REGISTER', 'UNDO'}

    collider_type: EnumProperty(
        name="Collider Type",
        items=[
            ('UBX_', "Box (UBX_)",     "Axis-aligned bounding box collider"),
            ('UCL_', "Capsule (UCL_)", "Capsule collider fitted to bounding box"),
        ],
        default='UBX_',
    )

    layer_preset: EnumProperty(
        name="Layer Preset",
        description="Enfusion layer preset for this collider",
        items=_COLLIDER_LAYER_ITEMS,
        default='Character',
    )

    def execute(self, context):
        mesh_objects = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        source = mesh_objects[0]

        base_name = source.name
        if base_name.upper().endswith("_LOD0"):
            base_name = base_name[:-5]

        collider_name = f"{self.collider_type}{base_name}"

        # Compute world-space bounding box corners
        from mathutils import Vector
        bbox_local = [Vector(v) for v in source.bound_box]
        bbox_world = [source.matrix_world @ v for v in bbox_local]

        xs = [v.x for v in bbox_world]
        ys = [v.y for v in bbox_world]
        zs = [v.z for v in bbox_world]

        center = Vector((
            (min(xs) + max(xs)) / 2,
            (min(ys) + max(ys)) / 2,
            (min(zs) + max(zs)) / 2,
        ))
        dims = Vector((max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)))

        if self.collider_type == 'UBX_':
            bpy.ops.mesh.primitive_cube_add(size=1, location=center)
            prim = context.active_object
            prim.scale = dims / 2
            bpy.ops.object.transform_apply(scale=True)
        else:
            # UCL_ — use a cylinder as a crude capsule approximation
            bpy.ops.mesh.primitive_cylinder_add(
                radius=max(dims.x, dims.y) / 2,
                depth=dims.z,
                location=center,
            )
            prim = context.active_object

        prim.name = collider_name
        if prim.data:
            prim.data.name = collider_name

        prim["usage"] = self.layer_preset
        prim.display_type = 'WIRE'

        self.report({'INFO'},
                    f"Created primitive collider '{collider_name}' "
                    f"with usage='{self.layer_preset}'")
        return {'FINISHED'}
