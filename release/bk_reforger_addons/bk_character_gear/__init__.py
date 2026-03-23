bl_info = {
    "name": "BK Character Gear",
    "author": "steffenbk",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BK Character Gear",
    "description": "Automate the Arma Reforger clothing/gear import pipeline for novice modelers",
    "category": "Object",
}

import bpy
from bpy.props import EnumProperty, StringProperty

from .constants import GEAR_TYPE_ITEMS

from .operators import (
    CHARGEAR_OT_import_gear,
    CHARGEAR_OT_bind_to_skeleton,
    CHARGEAR_OT_transfer_weights,
    CHARGEAR_OT_migrate_facial_weights,
    CHARGEAR_OT_create_gear_lods,
    CHARGEAR_OT_create_gear_collider,
    CHARGEAR_OT_create_primitive_collider,
    CHARGEAR_OT_validate_gear,
    CHARGEAR_OT_full_pipeline,
)

from .ui import CHARGEAR_PT_panel

classes = (
    CHARGEAR_OT_import_gear,
    CHARGEAR_OT_bind_to_skeleton,
    CHARGEAR_OT_transfer_weights,
    CHARGEAR_OT_migrate_facial_weights,
    CHARGEAR_OT_create_gear_lods,
    CHARGEAR_OT_create_gear_collider,
    CHARGEAR_OT_create_primitive_collider,
    CHARGEAR_OT_validate_gear,
    CHARGEAR_OT_full_pipeline,
    CHARGEAR_PT_panel,
)


def register():
    bpy.types.Scene.chargear_type = EnumProperty(
        name="Gear Type",
        description="Type of character gear being prepared",
        items=GEAR_TYPE_ITEMS,
        default='HEADGEAR',
    )
    bpy.types.Scene.chargear_name = StringProperty(
        name="Gear Name",
        description="Base name for the current gear asset (e.g. Ops_Core_Helmet)",
        default="Gear",
    )
    bpy.types.Scene.chargear_template_path = StringProperty(
        name="Template Path",
        description="Optional path to reference skeleton FBX for alignment/weight transfer",
        default="",
        subtype='FILE_PATH',
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    for prop in ('chargear_type', 'chargear_name', 'chargear_template_path'):
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
