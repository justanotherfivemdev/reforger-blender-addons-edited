import bpy
from bpy.types import Operator
from bpy.props import IntProperty, BoolProperty


class MESH_OT_crater_create_lods(Operator):
    """Create LOD levels for selected crater objects"""
    bl_idname = "mesh.crater_create_lods"
    bl_label = "Create LOD Levels"
    bl_options = {'REGISTER', 'UNDO'}

    lod_levels: IntProperty(
        name="LOD Levels",
        default=3,
        min=1,
        max=5,
        description="Number of LOD levels to create"
    )

    create_collection: BoolProperty(
        name="Create Collection",
        default=True,
        description="Organize LODs in a collection"
    )

    join_lod_levels: BoolProperty(
        name="Join LOD Levels",
        default=True,
        description="Join all parts of each LOD level into single objects"
    )

    aggressive_reduction: BoolProperty(
        name="Aggressive Reduction",
        default=True,
        description="Use more dramatic reduction ratios for visible LOD differences"
    )

    def execute(self, context):
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Get base name from first object or use "Crater" as default
        first_obj = mesh_objects[0]
        base_name = first_obj.name.replace("_LOD0", "").split("_")[0] if "_" in first_obj.name else "Crater"

        # Create collection if requested
        if self.create_collection:
            collection_name = f"{base_name}_LOD_Collection"
            # Check if collection already exists
            if collection_name not in bpy.data.collections:
                new_collection = bpy.data.collections.new(collection_name)
                context.scene.collection.children.link(new_collection)
            else:
                new_collection = bpy.data.collections[collection_name]

        # Improved reduction ratios for complex crater geometry
        if self.aggressive_reduction:
            ratios = [0.6, 0.35, 0.2, 0.12, 0.08]  # More conservative for complex meshes
        else:
            ratios = [0.75, 0.5, 0.3, 0.2, 0.15]  # Very conservative reduction

        created_lods = 0
        all_lod_objects = {i: [] for i in range(1, self.lod_levels + 1)}  # Track objects by LOD level

        # Process each selected object
        for source_obj in mesh_objects:
            obj_base_name = source_obj.name.replace("_LOD0", "")

            for lod in range(1, min(self.lod_levels + 1, 6)):  # Max 5 LODs
                # Duplicate from source
                bpy.ops.object.select_all(action='DESELECT')
                source_obj.select_set(True)
                context.view_layer.objects.active = source_obj

                bpy.ops.object.duplicate_move(
                    OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'},
                    TRANSFORM_OT_translate={"value": (0, 0, 0)}
                )

                lod_obj = context.active_object
                lod_obj.name = f"{obj_base_name}_LOD{lod}"

                # Pre-processing for complex crater meshes
                self.preprocess_crater_for_lod(lod_obj, lod)

                # Apply improved decimation for crater geometry
                self.apply_crater_decimation(lod_obj, ratios[lod - 1], lod)

                # Post-processing cleanup
                self.cleanup_lod_mesh(lod_obj)

                # Add to collection if enabled
                if self.create_collection:
                    if lod_obj.name in context.scene.collection.objects:
                        context.scene.collection.objects.unlink(lod_obj)
                    new_collection.objects.link(lod_obj)

                # Track for joining
                all_lod_objects[lod].append(lod_obj)
                created_lods += 1

        # Join LOD levels if requested
        if self.join_lod_levels:
            for lod_level, lod_objects in all_lod_objects.items():
                if len(lod_objects) > 1:  # Only join if multiple objects
                    self._join_lod_objects(lod_objects, f"{base_name}_LOD{lod_level}")

        # Rename source objects to LOD0
        for source_obj in mesh_objects:
            if "_LOD0" not in source_obj.name:
                source_obj.name = f"{source_obj.name}_LOD0"

            # Add source to collection too
            if self.create_collection:
                if source_obj.name in context.scene.collection.objects:
                    context.scene.collection.objects.unlink(source_obj)
                new_collection.objects.link(source_obj)

        # Select remaining LOD objects (avoid invalid references)
        bpy.ops.object.select_all(action='DESELECT')
        valid_lod_objects = []

        for obj_name in bpy.data.objects.keys():
            if "_LOD" in obj_name and any(obj_name.startswith(f"{base_name}_LOD") for base_name in [obj.name.split("_")[0] for obj in mesh_objects]):
                obj = bpy.data.objects[obj_name]
                obj.select_set(True)
                valid_lod_objects.append(obj)

        self.report({'INFO'}, f"Created {created_lods} LOD objects, joined into {len(valid_lod_objects)} final LOD levels")
        return {'FINISHED'}

    def preprocess_crater_for_lod(self, obj, lod_level):
        """Pre-process crater mesh to improve LOD generation"""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Remove doubles first to clean up overlapping vertices from complex generation
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.001)

        # For higher LOD levels, simplify small details that cause decimation issues
        if lod_level >= 3:
            # Smooth out extreme surface detail that causes decimation problems
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.vertices_smooth(factor=0.2)

        bpy.ops.object.mode_set(mode='OBJECT')

    def apply_crater_decimation(self, obj, target_ratio, lod_level):
        """Apply optimized decimation for crater geometry"""
        # Use different decimation strategies based on LOD level
        if lod_level <= 2:
            # For early LODs, use collapse decimation which preserves overall shape better
            decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.decimate_type = 'COLLAPSE'
            decimate.ratio = max(0.1, target_ratio)
            # Preserve crater rim and major features
            decimate.use_collapse_triangulate = True
        else:
            # For higher LODs, use unsubdivided decimation which is more predictable
            decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
            decimate.decimate_type = 'UNSUBDIV'
            decimate.iterations = min(3, lod_level)

            # Follow up with collapse if still too complex
            current_faces = len(obj.data.polygons)
            if current_faces > 200:  # Still too complex
                bpy.ops.object.modifier_apply(modifier=decimate.name)

                collapse_decimate = obj.modifiers.new(name="Decimate_Collapse", type='DECIMATE')
                collapse_decimate.decimate_type = 'COLLAPSE'
                collapse_decimate.ratio = min(0.3, 150 / current_faces)  # Target ~150 faces max
                bpy.ops.object.modifier_apply(modifier=collapse_decimate.name)
                return

        bpy.ops.object.modifier_apply(modifier=decimate.name)

    def cleanup_lod_mesh(self, obj):
        """Clean up LOD mesh after decimation"""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Clean up any resulting geometry issues
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.001)
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.fill_holes(sides=10)

        # Recalculate normals for proper shading
        bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.object.mode_set(mode='OBJECT')

    def _join_lod_objects(self, lod_objects, joined_name):
        """Join multiple LOD objects into a single object"""
        if not lod_objects:
            return

        # Select all objects for this LOD level
        bpy.ops.object.select_all(action='DESELECT')
        for obj in lod_objects:
            obj.select_set(True)

        # Set the first object as active
        bpy.context.view_layer.objects.active = lod_objects[0]

        # Join all selected objects
        bpy.ops.object.join()

        # Renamed the joined object
        joined_obj = bpy.context.active_object
        joined_obj.name = joined_name

        return joined_obj

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
