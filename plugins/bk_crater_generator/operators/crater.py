import bpy
import bmesh
import math
from mathutils import noise, Vector
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty, BoolProperty

# Derived constants from reference crater analysis
_SKIRT_DEPTH_RATIO = 0.85   # outer edge sits at -0.85 * rim_height
_SKIRT_CROSSOVER_T = 0.55   # outer skirt crosses z=0 at 55% of rim->outer span


class MESH_OT_add_crater(Operator):
    """Generate a game-ready crater mesh based on reference crater analysis"""
    bl_idname = "mesh.add_crater"
    bl_label = "Generate Crater"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    outer_radius: FloatProperty(name="Outer Radius", default=5.0, min=0.5, max=100.0)
    rim_radius: FloatProperty(name="Rim Radius", default=2.25, min=0.1, max=50.0)
    rim_height: FloatProperty(name="Rim Height", default=0.5, min=0.0, max=100.0)
    depth: FloatProperty(name="Depth", default=0.5, min=0.01, max=100.0)
    resolution: IntProperty(name="Resolution", default=32, min=8, max=512)
    noise_strength: FloatProperty(name="Surface Noise", default=0.02, min=0.0, max=5.0)
    create_materials: BoolProperty(name="Create Materials", default=True)
    auto_uv: BoolProperty(name="Auto UV", default=True)

    def execute(self, context):
        try:
            # Validate
            if self.rim_radius >= self.outer_radius:
                self.rim_radius = self.outer_radius * 0.45
                self.report({'INFO'}, f"Rim radius adjusted to {self.rim_radius:.2f} (must be < outer radius)")

            crater_data = self._generate_crater_mesh()
            if not crater_data:
                self.report({'ERROR'}, "Failed to generate crater mesh")
                return {'CANCELLED'}

            mesh = bpy.data.meshes.new("Crater")
            obj = bpy.data.objects.new("Crater", mesh)
            obj.location = context.scene.cursor.location

            mesh.from_pydata(crater_data['vertices'], [], crater_data['faces'])
            mesh.update()

            self._optimize_mesh(mesh)

            context.collection.objects.link(obj)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            if self.create_materials:
                self._setup_materials(obj)
            if self.auto_uv:
                self._generate_uvs(obj)

            self.report({'INFO'}, f"Crater: {len(mesh.polygons)} tris, {len(mesh.vertices)} verts")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Crater generation failed: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {'CANCELLED'}

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def _generate_crater_mesh(self):
        bm = bmesh.new()
        try:
            self._build_crater_geometry(bm)
            self._apply_surface_noise(bm)
            self._optimize_topology(bm)

            vertices = [[v.co.x, v.co.y, v.co.z] for v in bm.verts]
            faces = [[v.index for v in f.verts] for f in bm.faces]
            return {'vertices': vertices, 'faces': faces}
        finally:
            bm.free()

    def _build_crater_geometry(self, bm):
        """Build concentric rings from outer edge inward to center."""
        all_rings = []

        # --- Outer edge ring (r=outer_radius, z=-skirt_depth) ---
        skirt_depth = _SKIRT_DEPTH_RATIO * self.rim_height
        outer_edge_z = -skirt_depth
        all_rings.append(self._make_ring(bm, self.outer_radius, outer_edge_z))

        # --- Outer skirt rings (3 rings between rim and outer edge) ---
        for t in (0.66, 0.33):
            r = self.rim_radius + t * (self.outer_radius - self.rim_radius)
            z = self._skirt_z(t)
            all_rings.append(self._make_ring(bm, r, z))

        # --- Rim ring (peak) ---
        all_rings.append(self._make_ring(bm, self.rim_radius, self.rim_height))

        # --- Inner bowl rings (2 rings between rim and center) ---
        for t in (0.65, 0.35):
            r = t * self.rim_radius
            z = self._bowl_z(t)
            all_rings.append(self._make_ring(bm, r, z))

        # --- Center point ---
        center = bm.verts.new((0.0, 0.0, -self.depth))
        all_rings.append([center])

        # --- Connect rings ---
        for i in range(len(all_rings) - 1):
            outer_ring = all_rings[i]
            inner_ring = all_rings[i + 1]

            if len(inner_ring) == 1:
                for j in range(len(outer_ring)):
                    nj = (j + 1) % len(outer_ring)
                    bm.faces.new([outer_ring[j], outer_ring[nj], inner_ring[0]])
            else:
                failed_faces = 0
                for j in range(len(outer_ring)):
                    nj = (j + 1) % len(outer_ring)
                    try:
                        bm.faces.new([
                            outer_ring[j], outer_ring[nj],
                            inner_ring[nj], inner_ring[j]
                        ])
                    except Exception:
                        failed_faces += 1
                if failed_faces > 0:
                    print(f"Crater: {failed_faces} degenerate faces skipped in ring {i}")

        bm.normal_update()

    def _make_ring(self, bm, radius, z):
        """Create one ring of vertices at given radius and height."""
        verts = []
        for i in range(self.resolution):
            angle = 2.0 * math.pi * i / self.resolution
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            verts.append(bm.verts.new((x, y, z)))
        return verts

    def _bowl_z(self, t):
        """Inner bowl height at normalized parameter t (0=center, 1=rim).
        Power curve: slow rise from floor, accelerating toward rim peak.
        """
        return -self.depth + (self.depth + self.rim_height) * (t ** 1.5)


    def _skirt_z(self, t):
        """Outer skirt height at normalized parameter t (0=rim, 1=outer edge).
        Piecewise cosine: smooth from rim_height through z=0 to -skirt_depth.
        Crossover (z=0) at t=_SKIRT_CROSSOVER_T (~0.55), matching reference data.
        """
        skirt_depth = _SKIRT_DEPTH_RATIO * self.rim_height
        ct = _SKIRT_CROSSOVER_T

        if t <= ct:
            # rim_height -> 0
            local = t / ct
            ease = 0.5 - 0.5 * math.cos(local * math.pi)
            return self.rim_height * (1.0 - ease)
        else:
            # 0 -> -skirt_depth
            local = (t - ct) / (1.0 - ct)
            ease = 0.5 - 0.5 * math.cos(local * math.pi)
            return -skirt_depth * ease

    def _apply_surface_noise(self, bm):
        if self.noise_strength <= 0:
            return
        for vert in bm.verts:
            pos = vert.co
            n = (noise.noise(pos * 1.5) * 0.6 +
                 noise.noise(pos * 4.0) * 0.3 +
                 noise.noise(pos * 10.0) * 0.1)
            vert.co.z += n * self.noise_strength

    def _optimize_topology(self, bm):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=bm.faces,
                              quad_method='BEAUTY', ngon_method='BEAUTY')

    def _optimize_mesh(self, mesh):
        mesh.validate(verbose=False, clean_customdata=True)
        mesh.calc_loop_triangles()
        mesh.update()
        for poly in mesh.polygons:
            poly.use_smooth = True

    # ------------------------------------------------------------------
    # Materials
    # ------------------------------------------------------------------

    def _setup_materials(self, obj):
        try:
            obj.data.materials.clear()
            obj.data.materials.append(self._make_inner_material())
            obj.data.materials.append(self._make_outer_material())
            self._assign_materials(obj)
        except Exception as e:
            print(f"Material setup error: {e}")

    def _make_inner_material(self):
        mat = bpy.data.materials.new(name="Crater_Inner")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.15, 0.10, 0.08, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        return mat

    def _make_outer_material(self):
        mat = bpy.data.materials.new(name="Crater_Outer")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.50, 0.40, 0.30, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
        return mat

    def _assign_materials(self, obj):
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()

        inner_limit = self.rim_radius * 1.1

        for face in bm.faces:
            c = face.calc_center_median()
            r = math.sqrt(c.x ** 2 + c.y ** 2)
            # Inner material: inside rim area or above ground
            face.material_index = 0 if (r < inner_limit or c.z > 0) else 1

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

    # ------------------------------------------------------------------
    # UV
    # ------------------------------------------------------------------

    def _generate_uvs(self, obj):
        try:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')

            if not obj.data.uv_layers:
                bpy.ops.mesh.uv_texture_add()

            bpy.ops.uv.cylinder_project(
                direction='VIEW_ON_EQUATOR',
                align='POLAR_ZZ',
                scale_to_bounds=False,
                correct_aspect=True
            )
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.angle_based_unwrap(
                angle_limit=math.radians(66),
                margin=0.001
            )
            bpy.ops.uv.pack_islands(
                rotate=True,
                margin=0.01,
                scale=True,
                merge_overlap=False
            )
            bpy.ops.uv.remove_doubles(threshold=0.02, use_unselected=False)
            bpy.ops.object.mode_set(mode='OBJECT')

        except Exception as e:
            print(f"UV error: {e}")
            try:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.project_from_view(
                    camera_bounds=True, correct_aspect=True, scale_to_bounds=False
                )
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                bpy.ops.object.mode_set(mode='OBJECT')

    # ------------------------------------------------------------------
    # Invoke - copy PropertyGroup values to operator for redo panel
    # ------------------------------------------------------------------

    def invoke(self, context, event):
        if hasattr(context.scene, 'crater_properties'):
            props = context.scene.crater_properties
            self.outer_radius = props.outer_radius
            self.rim_radius = props.rim_radius
            self.rim_height = props.rim_height
            self.depth = props.depth
            self.resolution = props.resolution
            self.noise_strength = props.noise_strength
            self.create_materials = props.create_materials
            self.auto_uv = props.auto_uv
        return self.execute(context)
