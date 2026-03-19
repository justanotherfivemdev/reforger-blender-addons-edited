import bpy
import bmesh
import math
from collections import deque
from bpy.types import Operator
from bpy.props import FloatProperty

BLEND_ATTR = "crater_blend"


class MESH_OT_crater_blend_materials(Operator):
    """Paint a vertex-color blend mask between material 0 and material 1"""
    bl_idname = "mesh.crater_blend_materials"
    bl_label = "Blend Materials"
    bl_options = {'REGISTER', 'UNDO'}

    blend_width: FloatProperty(
        name="Blend Width",
        description="Distance (m) over which materials cross-fade at the seam",
        default=0.5,
        min=0.01,
        max=20.0,
        unit='LENGTH',
        step=10
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if len(obj.data.materials) < 2:
            self.report({'ERROR'}, "Mesh needs at least 2 materials")
            return {'CANCELLED'}

        # Must be in object mode to write back to mesh
        was_edit = (obj.mode == 'EDIT')
        if was_edit:
            bpy.ops.object.mode_set(mode='OBJECT')

        mesh = obj.data

        # Remove existing attribute if present
        if BLEND_ATTR in mesh.attributes:
            mesh.attributes.remove(mesh.attributes[BLEND_ATTR])

        # Build bmesh to query topology
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        n_verts = len(bm.verts)

        # --- Find seam edges: one face mat0, other face mat1 ---
        seam_verts = set()
        for edge in bm.edges:
            linked = edge.link_faces
            if len(linked) == 2:
                m0 = linked[0].material_index
                m1 = linked[1].material_index
                if (m0 == 0 and m1 == 1) or (m0 == 1 and m1 == 0):
                    seam_verts.add(edge.verts[0].index)
                    seam_verts.add(edge.verts[1].index)

        if not seam_verts:
            self.report({'WARNING'}, "No seam found between material 0 and material 1")
            bm.free()
            return {'CANCELLED'}

        # --- BFS distance from seam, clamped to blend_width ---
        # Store 3D distance from nearest seam vertex for each vert
        dist = [float('inf')] * n_verts
        queue = deque()

        for vi in seam_verts:
            dist[vi] = 0.0
            queue.append(vi)

        # Build adjacency list
        adj = [[] for _ in range(n_verts)]
        for edge in bm.edges:
            a = edge.verts[0].index
            b = edge.verts[1].index
            adj[a].append(b)
            adj[b].append(a)

        # BFS propagating actual 3D distances
        while queue:
            vi = queue.popleft()
            v_co = bm.verts[vi].co
            for ni in adj[vi]:
                d = dist[vi] + (bm.verts[ni].co - v_co).length
                if d < dist[ni]:
                    dist[ni] = d
                    queue.append(ni)

        # --- Determine which side each vertex belongs to ---
        # Walk from seam: face mat_index tells us which side a vert is on.
        # For each vert, majority material of its faces (excluding seam verts = 0.5)
        side = [None] * n_verts  # 0 = mat0 side, 1 = mat1 side
        for vert in bm.verts:
            if vert.index in seam_verts:
                side[vert.index] = -1  # seam itself
                continue
            counts = [0, 0]
            for face in vert.link_faces:
                mi = face.material_index
                if mi < 2:
                    counts[mi] += 1
            side[vert.index] = 0 if counts[0] >= counts[1] else 1

        # --- Compute blend value ---
        # Mat0 side: 0.0 (fully mat0)  Mat1 side: 1.0 (fully mat1)
        # Seam and within blend_width: smooth 0.5 cosine ramp
        values = [0.0] * n_verts
        half = self.blend_width * 0.5

        for i in range(n_verts):
            s = side[i]
            d = min(dist[i], half)
            t = d / half if half > 0 else 1.0
            ramp = 0.5 - 0.5 * math.cos(t * math.pi)  # 0→1 ease

            if s == -1:
                values[i] = 0.5
            elif s == 0:
                # mat0 side: starts at 0.5 at seam, goes to 0.0
                values[i] = 0.5 * (1.0 - ramp)
            else:
                # mat1 side: starts at 0.5 at seam, goes to 1.0
                values[i] = 0.5 + 0.5 * ramp

        # Write values into a bmesh float layer, then flush to mesh
        layer = bm.verts.layers.float.new(BLEND_ATTR)
        for i, vert in enumerate(bm.verts):
            vert[layer] = values[i]

        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        if was_edit:
            bpy.ops.object.mode_set(mode='EDIT')

        self.report({'INFO'}, f"Blend mask written to '{BLEND_ATTR}' ({len(seam_verts)} seam verts)")
        return {'FINISHED'}
