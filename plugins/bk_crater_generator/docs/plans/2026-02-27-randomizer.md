# Crater Randomizer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a type-constrained randomizer (Small / Standard / Artillery) that samples measured reference ranges and generates a crater in one click.

**Architecture:** New `EnumProperty` on `CraterProperties` selects the crater type. A new `MESH_OT_randomize_crater` operator reads that type, samples parameters with `random.uniform` within reference-derived ranges, writes values back to `CraterProperties`, then calls the existing `mesh.add_crater` operator. Panel gets the enum row at the top and a Randomize button below Generate.

**Tech Stack:** Blender Python API (`bpy`, `bpy.props`, `bpy.types.Operator`), Python `random` stdlib.

---

### Task 1: Add `crater_type` enum to CraterProperties

**Files:**
- Modify: `plugins/bk_crater_generator/properties.py`

**Step 1: Add import**

At the top of `properties.py`, add `EnumProperty` to the import:

```python
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
```

**Step 2: Add the property to `CraterProperties`**

Add this block after the existing `auto_uv` property (before the class ends):

```python
    crater_type: EnumProperty(
        name="Crater Type",
        description="Reference type used for randomization",
        items=[
            ('SMALL',     'Small',     'Small blast crater (5-12m)'),
            ('STANDARD',  'Standard',  'Standard explosion crater (15-35m)'),
            ('ARTILLERY', 'Artillery', 'Heavy artillery crater (20-40m, deep)'),
        ],
        default='STANDARD',
    )
```

**Step 3: Verify in Blender**

Reload the addon in Blender (Edit > Preferences > Add-ons, disable/enable BK Crater). Open the Create panel — the enum should NOT appear yet (panel not updated). No errors in console.

---

### Task 2: Create `operators/randomize.py`

**Files:**
- Create: `plugins/bk_crater_generator/operators/randomize.py`

**Step 1: Write the file**

```python
import bpy
import random
from bpy.types import Operator

# Ranges derived from reference crater mesh analysis (9 objects sampled)
_RANGES = {
    'SMALL': {
        'outer_radius':    (5.0,  12.0),
        'rim_r_ratio':     (0.45,  0.55),
        'rim_height':      (0.3,   0.8),
        'depth_rim_ratio': (1.8,   2.5),
        'resolution':      (24,    32),
    },
    'STANDARD': {
        'outer_radius':    (15.0, 35.0),
        'rim_r_ratio':     (0.35,  0.55),
        'rim_height':      (0.4,   1.2),
        'depth_rim_ratio': (0.85,  1.1),
        'resolution':      (28,    48),
    },
    'ARTILLERY': {
        'outer_radius':    (20.0, 40.0),
        'rim_r_ratio':     (0.38,  0.50),
        'rim_height':      (0.2,   0.6),
        'depth_rim_ratio': (4.5,   7.5),
        'resolution':      (32,    64),
    },
}


class MESH_OT_randomize_crater(Operator):
    """Randomize crater parameters based on the selected crater type"""
    bl_idname = "mesh.randomize_crater"
    bl_label = "Randomize Crater"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.crater_properties
        r = _RANGES[props.crater_type]

        outer_radius = random.uniform(*r['outer_radius'])
        rim_r_ratio  = random.uniform(*r['rim_r_ratio'])
        rim_height   = random.uniform(*r['rim_height'])
        depth        = rim_height * random.uniform(*r['depth_rim_ratio'])
        resolution   = random.randint(*r['resolution'])
        noise        = random.uniform(0.01, 0.05)

        props.outer_radius   = outer_radius
        props.rim_radius     = outer_radius * rim_r_ratio
        props.rim_height     = rim_height
        props.depth          = depth
        props.resolution     = resolution
        props.noise_strength = noise

        bpy.ops.mesh.add_crater(
            outer_radius=props.outer_radius,
            rim_radius=props.rim_radius,
            rim_height=props.rim_height,
            depth=props.depth,
            resolution=props.resolution,
            noise_strength=props.noise_strength,
            create_materials=props.create_materials,
            auto_uv=props.auto_uv,
        )

        self.report({'INFO'}, f"Random {props.crater_type.capitalize()} crater generated")
        return {'FINISHED'}
```

---

### Task 3: Register the new operator

**Files:**
- Modify: `plugins/bk_crater_generator/operators/__init__.py`

**Step 1: Add import and class**

```python
from .crater import MESH_OT_add_crater
from .firegeo import MESH_OT_crater_create_firegeo_collision
from .lods import MESH_OT_crater_create_lods
from .randomize import MESH_OT_randomize_crater

classes = (
    MESH_OT_add_crater,
    MESH_OT_randomize_crater,
    MESH_OT_crater_create_firegeo_collision,
    MESH_OT_crater_create_lods,
)
```

---

### Task 4: Update the panel

**Files:**
- Modify: `plugins/bk_crater_generator/ui/panels.py`

**Step 1: Add crater_type enum row and Randomize button**

Replace the `draw` method's top section. The new layout order:

1. `crater_type` enum (full row, at very top)
2. Generate button (existing, scale_y=1.8)
3. Randomize button (scale_y=1.4, below Generate)
4. Separator
5. Game Integration box (unchanged)
6. Separator
7. Dimensions box (unchanged)
8. Surface box (unchanged)
9. Output box (unchanged)

Full updated `draw` method:

```python
    def draw(self, context):
        layout = self.layout
        props = context.scene.crater_properties

        # Type selector
        layout.prop(props, "crater_type", text="Type")

        # Generate button
        row = layout.row()
        row.scale_y = 1.8
        op = row.operator("mesh.add_crater", text="Generate Crater", icon='OUTLINER_OB_META')
        op.outer_radius = props.outer_radius
        op.rim_radius = props.rim_radius
        op.rim_height = props.rim_height
        op.depth = props.depth
        op.resolution = props.resolution
        op.noise_strength = props.noise_strength
        op.create_materials = props.create_materials
        op.auto_uv = props.auto_uv

        # Randomize button
        row = layout.row()
        row.scale_y = 1.4
        row.operator("mesh.randomize_crater", text="Randomize", icon='FILE_REFRESH')

        layout.separator()

        # Game integration
        box = layout.box()
        box.label(text="Game Integration", icon='TOOL_SETTINGS')
        col = box.column(align=True)
        col.operator("mesh.crater_create_firegeo_collision",
                     text="Create FireGeo Collision", icon='PHYSICS')
        col.operator("mesh.crater_create_lods",
                     text="Create LOD Levels", icon='MOD_DECIM')

        layout.separator()

        # Dimensions
        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CIRCLE')
        col = box.column(align=True)
        col.prop(props, "outer_radius")
        col.prop(props, "rim_radius")
        col.prop(props, "rim_height")
        col.prop(props, "depth")
        col.prop(props, "resolution")
        estimated_tris = props.resolution * 11
        box.label(text=f"~{estimated_tris} triangles", icon='INFO')

        # Surface
        box = layout.box()
        box.label(text="Surface", icon='TEXTURE')
        box.prop(props, "noise_strength")

        # Output
        box = layout.box()
        box.label(text="Output", icon='EXPORT')
        col = box.column(align=True)
        col.prop(props, "create_materials")
        col.prop(props, "auto_uv")
```

**Step 2: Reload addon and verify**

Reload the addon. The panel should show:
- Type enum at top (Small / Standard / Artillery)
- Generate button
- Randomize button
- Rest of panel unchanged

Click Randomize several times with each type — verify crater sizes match the expected ranges and panel values update after each click.
