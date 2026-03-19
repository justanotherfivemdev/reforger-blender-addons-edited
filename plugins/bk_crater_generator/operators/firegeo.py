import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty, FloatProperty


class MESH_OT_crater_create_firegeo_collision(Operator):
    """Create FireGeo collision for selected crater objects"""
    bl_idname = "mesh.crater_create_firegeo_collision"
    bl_label = "Create FireGeo Collision"
    bl_options = {'REGISTER', 'UNDO'}

    method: EnumProperty(
        name="Method",
        items=[
            ('CONVEX', "Convex Hull", "Simplified convex hull"),
            ('DETAILED', "Detailed", "Preserves shape better"),
        ],
        default='DETAILED'
    )
    layer_preset: EnumProperty(
        name="Layer Preset",
        description="Enfusion collision layer preset",
        items=[
            ('FireGeo', "FireGeo", "FireGeometry only"),
            ('FireView', "FireView", "FireGeometry + ViewGeometry"),
            ('PropFireView', "PropFireView", "Dynamic + FireGeo + ViewGeometry + NavmeshVehicle"),
            ('BuildingFireView', "BuildingFireView", "Static + FireGeo + ViewGeometry + Navmesh"),
        ],
        default='FireGeo'
    )
    target_faces: IntProperty(name="Target Faces", default=400, min=100, max=5000)
    offset: FloatProperty(name="Offset", default=0.01, min=0.0, max=0.05)

    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        collision_objects = []
        total_faces = 0

        # Create or get BuildingFireView collection
        collection_name = self.layer_preset
        if collection_name not in bpy.data.collections:
            fireview_collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(fireview_collection)
        else:
            fireview_collection = bpy.data.collections[collection_name]

        for idx, source_obj in enumerate(mesh_objects):
            bpy.ops.object.select_all(action='DESELECT')
            source_obj.select_set(True)
            context.view_layer.objects.active = source_obj

            bpy.ops.object.duplicate()
            dup_obj = context.selected_objects[0]

            if len(mesh_objects) == 1:
                dup_obj.name = "UTM_crater"
            else:
                dup_obj.name = f"UTM_crater_part_{idx}"

            collision_objects.append(dup_obj)

            part_target_faces = int(self.target_faces / len(mesh_objects))
            current_faces = len(dup_obj.data.polygons)

            if current_faces > part_target_faces:
                obj_dimensions = dup_obj.dimensions
                is_flat = min(obj_dimensions) < max(obj_dimensions) * 0.1

                if is_flat:
                    target_ratio = max(0.8, part_target_faces / current_faces)
                else:
                    target_ratio = part_target_faces / current_faces

                if target_ratio < 1.0:
                    decimate = dup_obj.modifiers.new(name="Decimate", type='DECIMATE')
                    decimate.ratio = max(0.1, target_ratio)
                    bpy.ops.object.modifier_apply(modifier=decimate.name)

            if self.offset > 0:
                solidify = dup_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
                solidify.thickness = self.offset
                solidify.offset = 1.0
                bpy.ops.object.modifier_apply(modifier=solidify.name)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            obj_dimensions = dup_obj.dimensions
            is_flat = min(obj_dimensions) < max(obj_dimensions) * 0.1
            merge_threshold = 0.0001 if is_flat else 0.001
            bpy.ops.mesh.remove_doubles(threshold=merge_threshold)
            bpy.ops.object.mode_set(mode='OBJECT')

            # Create or use the specific dirt material for FireGeo collision
            mat_name = "dirt_C3691F2D8FE0234F"
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
            else:
                # Create fallback FireGeo material if specific dirt material doesn't exist
                if "FireGeo_Material" not in bpy.data.materials:
                    mat = bpy.data.materials.new(name="FireGeo_Material")
                    mat.diffuse_color = (0.0, 0.8, 0.0, 0.5)
                else:
                    mat = bpy.data.materials["FireGeo_Material"]

            dup_obj.data.materials.clear()
            dup_obj.data.materials.append(mat)
            dup_obj["layer_preset"] = self.layer_preset
            dup_obj["usage"] = self.layer_preset

            # Move to BuildingFireView collection
            if dup_obj.name in context.scene.collection.objects:
                context.scene.collection.objects.unlink(dup_obj)
            fireview_collection.objects.link(dup_obj)

            total_faces += len(dup_obj.data.polygons)

        # Select all collision objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collision_objects:
            obj.select_set(True)

        if collision_objects:
            context.view_layer.objects.active = collision_objects[0]

        self.report({'INFO'}, f"Created FireGeo collision with {total_faces} total faces")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
