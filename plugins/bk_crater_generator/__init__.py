bl_info = {
    "name": "BK Crater",
    "author": "steffenbk",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Add > Mesh > Game Crater",
    "description": "Generate clean game-ready crater meshes with dual materials, optimized UV mapping, FireGeo collision and LODs",
    "category": "Add Mesh",
    "doc_url": "",
    "tracker_url": "",
}

import bpy
from bpy.props import PointerProperty

from .properties import CraterProperties
from .operators import classes as operator_classes
from .ui import classes as ui_classes

classes = (
    CraterProperties,
    *operator_classes,
    *ui_classes,
)


def menu_func(self, context):
    """Add crater to the Add > Mesh menu"""
    self.layout.operator("mesh.add_crater", text="Game Crater", icon='OUTLINER_OB_META')


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.crater_properties = PointerProperty(type=CraterProperties)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    if hasattr(bpy.types.Scene, 'crater_properties'):
        del bpy.types.Scene.crater_properties

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
