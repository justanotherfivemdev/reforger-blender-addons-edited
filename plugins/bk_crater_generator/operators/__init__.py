from .crater import MESH_OT_add_crater
from .reset import MESH_OT_crater_reset_defaults
from .blend import MESH_OT_crater_blend_materials
from .assign_mat import MESH_OT_crater_assign_material
from .firegeo import MESH_OT_crater_create_firegeo_collision
from .lods import MESH_OT_crater_create_lods

classes = (
    MESH_OT_add_crater,
    MESH_OT_crater_reset_defaults,
    MESH_OT_crater_blend_materials,
    MESH_OT_crater_assign_material,
    MESH_OT_crater_create_firegeo_collision,
    MESH_OT_crater_create_lods,
)
