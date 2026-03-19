# Crater Randomizer Design

Date: 2026-02-27

## Goal

Add a type-constrained randomizer to the crater generator. The user picks a crater type (Small / Standard / Artillery) and clicks Randomize — the operator samples parameter values from measured reference ranges, writes them back to the panel properties, then generates a crater.

## Reference Data

Ranges derived from sampling 9 reference crater meshes in Blender (SM_CraterA/B/C variants, 16-inch artillery craters, Crete variants):

| Type      | outer_radius (m) | rim_r % of outer | rim_height (m) | depth / rim_height ratio | resolution |
|-----------|-----------------|------------------|----------------|--------------------------|------------|
| Small     | 5–12            | 45–55%           | 0.3–0.8        | 1.8–2.5                  | 24–32      |
| Standard  | 15–35           | 35–55%           | 0.4–1.2        | 0.85–1.1                 | 28–48      |
| Artillery | 20–40           | 38–50%           | 0.2–0.6        | 4.5–7.5                  | 32–64      |

Derived values: `rim_radius = outer_radius * rim_r_ratio`, `depth = rim_height * depth_rim_ratio`.
`noise_strength` randomized 0.01–0.05 for all types.
`create_materials` and `auto_uv` are left untouched.

## Components

### properties.py
- Add `crater_type: EnumProperty` with items Small / Standard / Artillery, default Standard.

### operators/randomize.py (new file)
- `MESH_OT_randomize_crater` (`mesh.randomize_crater`)
- Reads `crater_type` from `context.scene.crater_properties`
- Samples parameters using `random.uniform` within type ranges
- Writes results back to props
- Calls `bpy.ops.mesh.add_crater()`

### operators/__init__.py
- Import and register `MESH_OT_randomize_crater`

### ui/panels.py
- `crater_type` enum row at top of panel (above Generate button)
- "Randomize" button row below Generate button
