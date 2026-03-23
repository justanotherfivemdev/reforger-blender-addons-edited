import os
import bpy
from bpy.props import StringProperty

from ..constants import (
    CHARACTER_SKELETON_BONES,
    CHARACTER_SKELETON_BONE_SET,
    CHAR_TEMPLATE_PREFIX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_template_collection(scene):
    """
    Return (or create) the 'Character Template' collection inside *scene*.
    The collection is created as a child of the master collection so it
    appears in the Outliner but is clearly segregated from gear objects.
    """
    coll_name = "Character Template"
    coll = bpy.data.collections.get(coll_name)
    if coll is None:
        coll = bpy.data.collections.new(coll_name)
        scene.collection.children.link(coll)
    elif coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def _template_objects(scene):
    """Yield all objects in *scene* that carry the CHAR_TEMPLATE_ prefix."""
    for obj in scene.objects:
        if obj.name.startswith(CHAR_TEMPLATE_PREFIX):
            yield obj


# ---------------------------------------------------------------------------
# Operator: Load Character Template
# ---------------------------------------------------------------------------

class CHARGEAR_OT_load_character_template(bpy.types.Operator):
    """
    Load Character_Weights_Template.blend (the official BI reference file) into
    the current scene as a non-selectable wire-display visual reference.

    The loaded objects are:
      • Placed in a dedicated 'Character Template' collection.
      • Renamed with the CHAR_TEMPLATE_ prefix so they can be cleaned up.
      • Set to wire display and hidden from selection — they will not
        interfere with normal editing of your gear mesh.

    Once loaded, the armature's bone names are cross-referenced against the
    plug-in's known skeleton list to surface any naming discrepancies.

    You can remove the template at any time with the 'Remove Template' button.
    """
    bl_idname = "chargear.load_character_template"
    bl_label = "Load Character Template"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.blend", options={'HIDDEN'})

    def invoke(self, context, event):
        # Pre-fill with the stored template path when available
        stored = context.scene.chargear_template_path
        if stored and os.path.isfile(stored):
            self.filepath = stored
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, "No file selected")
            return {'CANCELLED'}

        if not self.filepath.lower().endswith('.blend'):
            self.report({'ERROR'}, "Please select a .blend file")
            return {'CANCELLED'}

        if not os.path.isfile(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}

        # ── Load objects from the .blend library ────────────────────────────
        try:
            with bpy.data.libraries.load(self.filepath, link=False) as (src, dst):
                dst.objects = src.objects[:]
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to read template file: {exc}")
            return {'CANCELLED'}

        if not dst.objects:
            self.report({'WARNING'}, "No objects found in the template file")
            return {'CANCELLED'}

        # ── Prepare destination collection ───────────────────────────────────
        template_coll = _get_or_create_template_collection(context.scene)

        template_armature = None
        loaded = 0

        for obj in dst.objects:
            if obj is None:
                continue

            # Rename with prefix (avoid double-prefixing on re-load)
            if not obj.name.startswith(CHAR_TEMPLATE_PREFIX):
                obj.name = CHAR_TEMPLATE_PREFIX + obj.name

            # Link to the template collection (avoid duplicate links)
            if obj.name not in template_coll.objects:
                template_coll.objects.link(obj)

            # Visual settings: wire-frame, non-selectable, hidden from render
            obj.hide_select = True
            obj.hide_render = True
            obj.display_type = 'WIRE'

            if obj.type == 'ARMATURE':
                # Show the armature as a visible in-front overlay
                obj.show_in_front = True
                template_armature = obj

            loaded += 1

        # ── Save the path for future use ─────────────────────────────────────
        context.scene.chargear_template_path = self.filepath

        # ── Cross-reference bone names ───────────────────────────────────────
        if template_armature is not None:
            template_bone_names = {b.name for b in template_armature.data.bones}
            known_bones = CHARACTER_SKELETON_BONE_SET

            extra   = template_bone_names - known_bones   # in template, not in list
            missing = known_bones - template_bone_names   # in list, not in template

            if extra:
                sample = ", ".join(sorted(extra)[:6])
                suffix = "..." if len(extra) > 6 else ""
                self.report(
                    {'INFO'},
                    f"Template has {len(extra)} unrecognised bone(s) — "
                    f"update constants.py if needed: {sample}{suffix}"
                )

            if missing:
                sample = ", ".join(sorted(missing)[:6])
                suffix = "..." if len(missing) > 6 else ""
                self.report(
                    {'INFO'},
                    f"Known list has {len(missing)} bone(s) absent from the template — "
                    f"may be safe to remove: {sample}{suffix}"
                )

            bone_count = len(template_bone_names)
            self.report(
                {'INFO'},
                f"Loaded character template ({bone_count} bones) from "
                f"'{os.path.basename(self.filepath)}' — "
                f"{loaded} object(s) added to 'Character Template' collection"
            )
        else:
            self.report(
                {'INFO'},
                f"Loaded {loaded} object(s) from template "
                f"(no armature found — bone names not validated)"
            )

        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Operator: Remove Character Template
# ---------------------------------------------------------------------------

class CHARGEAR_OT_remove_character_template(bpy.types.Operator):
    """Remove all character template objects from the scene"""
    bl_idname = "chargear.remove_character_template"
    bl_label = "Remove Character Template"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Gather template objects from this scene
        to_remove = list(_template_objects(context.scene))
        if not to_remove:
            self.report({'INFO'}, "No character template objects found in the scene")
            return {'FINISHED'}

        removed = 0
        for obj in to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1

        # Remove the empty collection if it exists
        coll = bpy.data.collections.get("Character Template")
        if coll is not None and len(coll.objects) == 0:
            bpy.data.collections.remove(coll)

        self.report({'INFO'}, f"Removed {removed} character template object(s)")
        return {'FINISHED'}
