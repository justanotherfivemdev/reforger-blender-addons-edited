# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Panel

from ..curve_utils import _get_curve_mapping
from ..utils import _ensure_anchors


# ---------------------------------------------------------------------------
# UILists
# ---------------------------------------------------------------------------

class WG_UL_saved_curves(bpy.types.UIList):
    bl_idname = "WG_UL_saved_curves"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='CURVE_DATA')
        row.label(text=f"({item.point_count}pt)")
        op_del = row.operator("mesh.wg_delete_curve", text="", icon='X')
        op_del.index = index


class WG_UL_saved_selections(bpy.types.UIList):
    bl_idname = "WG_UL_saved_selections"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='RESTRICT_SELECT_OFF')
        row.label(text=f"({item.count})")
        op_del = row.operator("mesh.wg_delete_selection", text="", icon='X')
        op_del.index = index

    def filter_items(self, context, data, propname):
        sets = getattr(data, propname)
        if (not data.saved_selection_groups
                or data.active_selection_group_index < 0
                or data.active_selection_group_index >= len(data.saved_selection_groups)):
            return [self.bitflag_filter_item] * len(sets), []
        active_name = data.saved_selection_groups[data.active_selection_group_index].name
        flt_flags = [
            self.bitflag_filter_item if (s.group_name == active_name or s.group_name == "") else 0
            for s in sets
        ]
        return flt_flags, []


class WG_UL_selection_groups(bpy.types.UIList):
    bl_idname = "WG_UL_selection_groups"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        props = context.scene.weight_gradient
        count = sum(1 for s in props.saved_selections if s.group_name == item.name)
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='FILE_FOLDER')
        row.label(text=f"({count})")
        op_del = row.operator("mesh.wg_delete_selection_group", text="", icon='X')
        op_del.index = index


class WG_UL_anchor_groups(bpy.types.UIList):
    bl_idname = "WG_UL_anchor_groups"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        props = context.scene.weight_gradient
        count = sum(1 for s in props.saved_anchor_sets if s.group_name == item.name)
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='FILE_FOLDER')
        row.label(text=f"({count})")
        op_del = row.operator("mesh.wg_delete_anchor_group", text="", icon='X')
        op_del.index = index


class WG_UL_saved_anchor_sets(bpy.types.UIList):
    bl_idname = "WG_UL_saved_anchor_sets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='ANCHOR_CENTER')
        row.label(text=f"({item.anchor_count})")
        op_del = row.operator("mesh.wg_delete_anchor_set", text="", icon='X')
        op_del.index = index

    def filter_items(self, context, data, propname):
        sets = getattr(data, propname)
        if (not data.saved_anchor_groups
                or data.active_anchor_group_index < 0
                or data.active_anchor_group_index >= len(data.saved_anchor_groups)):
            return [self.bitflag_filter_item] * len(sets), []
        active_name = data.saved_anchor_groups[data.active_anchor_group_index].name
        flt_flags = [
            self.bitflag_filter_item if (s.group_name == active_name or s.group_name == "") else 0
            for s in sets
        ]
        return flt_flags, []


class WG_UL_full_presets(bpy.types.UIList):
    bl_idname = "WG_UL_full_presets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='PRESET')
        op_del = row.operator("mesh.wg_delete_full_preset", text="", icon='X')
        op_del.index = index


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _poll_mesh(cls, context):
    return (context.active_object is not None
            and context.active_object.type == 'MESH')


def _draw_anchor_row(layout, anchor, index):
    """Draw a single anchor row: [Set Anchor N] [status] [select btn] + weight slider."""
    box = layout.box()
    row = box.row(align=True)
    op = row.operator("mesh.wg_set_anchor", text=f"Set Anchor {index + 1}",
                      icon='VERTEXSEL')
    op.index = index
    if anchor.is_set:
        n = anchor.vert_count
        row.label(text=f"{n} vert{'s' if n > 1 else ''}", icon='CHECKMARK')
        sel = row.operator("mesh.wg_select_anchor_verts", text="",
                           icon='RESTRICT_SELECT_OFF')
        sel.index = index
    else:
        row.label(text="Not set", icon='X')
    box.prop(anchor, "weight", slider=True)


# ---------------------------------------------------------------------------
# Main panel — Source + Anchors + Group + Apply
# ---------------------------------------------------------------------------

class VIEW3D_PT_weight_gradient(Panel):
    bl_label = "Weight Gradient"
    bl_idname = "VIEW3D_PT_weight_gradient"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BK Weight Gradient"

    poll = classmethod(_poll_mesh)

    def draw(self, context):
        layout = self.layout
        props = context.scene.weight_gradient
        obj = context.active_object

        # -- Gradient Source toggle -----------------------------------------
        row = layout.row(align=True)
        row.prop(props, "gradient_source", expand=True)

        # -- Source-specific setup ------------------------------------------
        if props.gradient_source == 'AXIS':
            box_axis = layout.box()
            row = box_axis.row(align=True)
            row.label(text="Axis:")
            row.prop(props, "gradient_axis", expand=True)

            row = box_axis.row(align=True)
            row.label(text="Space:")
            row.prop(props, "gradient_space", expand=True)

            # Anchors are optional in axis mode — they clamp the range
            _ensure_anchors(props)
            header = layout.row(align=True)
            header.label(text="Range Anchors (optional):", icon='ANCHOR_CENTER')
            for i, a in enumerate(props.anchors[:2]):
                _draw_anchor_row(layout, a, i)

        else:  # ANCHORS
            layout.prop(props, "anchor_count")
            _ensure_anchors(props)
            for i, a in enumerate(props.anchors):
                _draw_anchor_row(layout, a, i)

        layout.separator()

        # -- Vertex group ---------------------------------------------------
        if obj.vertex_groups:
            layout.prop(props, "target_vg_name", text="Group")
        else:
            layout.label(text="No vertex groups", icon='ERROR')

        # -- Offset + Noise -------------------------------------------------
        row = layout.row(align=True)
        row.prop(props, "weight_offset", slider=True)
        row.prop(props, "gradient_noise", slider=True)

        layout.separator()

        # -- Apply + Flip + Select Last -------------------------------------
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("mesh.wg_apply_gradient", icon='MOD_VERTEX_WEIGHT')
        row.operator("mesh.wg_flip_gradient", text="", icon='ARROW_LEFTRIGHT')
        sub = row.row(align=True)
        sub.enabled = bool(props.last_gradient_indices_json)
        sub.operator("mesh.wg_select_last_gradient", text="", icon='RESTRICT_SELECT_OFF')

        layout.operator("mesh.wg_clear_anchors", icon='TRASH')


# ---------------------------------------------------------------------------
# Curve Settings sub-panel
# ---------------------------------------------------------------------------

class VIEW3D_PT_wg_curve(Panel):
    bl_label = "Curve Settings"
    bl_idname = "VIEW3D_PT_wg_curve"
    bl_parent_id = "VIEW3D_PT_weight_gradient"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BK Weight Gradient"

    poll = classmethod(_poll_mesh)

    def draw(self, context):
        layout = self.layout
        props = context.scene.weight_gradient

        row = layout.row(align=True)
        row.prop(props, "curve_mode", expand=True)

        if props.curve_mode == 'SIMPLE':
            row = layout.row(align=True)
            if props.curve_symmetry:
                row.prop(props, "simple_start", slider=True, text="Peak")
                row.prop(props, "simple_end", slider=True, text="Edge")
            else:
                row.prop(props, "simple_start", slider=True)
                row.prop(props, "simple_end", slider=True)
            row = layout.row(align=True)
            row.prop(props, "simple_shape", slider=True)
            row.prop(props, "curve_symmetry", text="", icon='MOD_MIRROR', toggle=True)

        elif props.curve_mode == 'CURVE_GRAPH':
            row = layout.row(align=True)
            row.prop(props, "curve_symmetry", text="Symmetric", icon='MOD_MIRROR', toggle=True)

            brush = _get_curve_mapping()
            if brush:
                layout.label(text="X = position (A\u2192B)   Y = weight value", icon='INFO')
                layout.template_curve_mapping(brush, "curve")
                layout.operator("mesh.wg_init_curve_from_anchors", icon='ANCHOR_CENTER')
            else:
                layout.label(text="Apply a preset to initialise the curve", icon='INFO')

            row = layout.row(align=True)
            for key in ('LINEAR', 'EASE_IN', 'EASE_OUT', 'S_CURVE'):
                op = row.operator("mesh.wg_curve_preset", text=key.replace('_', ' ').title())
                op.preset = key
            row = layout.row(align=True)
            for key in ('BELL', 'VALLEY', 'STEPS_3', 'SHARP_IN', 'SHARP_OUT'):
                op = row.operator("mesh.wg_curve_preset", text=key.replace('_', ' ').title())
                op.preset = key

            # Saved curves
            layout.separator()
            layout.label(text="Saved Curves:", icon='CURVE_DATA')
            layout.template_list(
                "WG_UL_saved_curves", "",
                props, "saved_curves",
                props, "active_curve_index",
                rows=2, maxrows=5,
            )
            row = layout.row(align=True)
            row.operator("mesh.wg_save_curve", text="Save", icon='ADD')
            sub = row.row(align=True)
            sub.enabled = len(props.saved_curves) > 0
            op = sub.operator("mesh.wg_load_curve", text="Load", icon='CHECKMARK')
            op.index = props.active_curve_index

        else:  # CONTROL_POINTS
            row = layout.row(align=True)
            row.prop(props, "segments")
            row.operator("mesh.wg_sync_points", text="", icon='FILE_REFRESH')
            row.operator("mesh.wg_reset_cp", text="", icon='LOOP_BACK')
            n_segs = props.segments
            n_pts = len(props.control_points)
            if n_pts >= 2:
                row.prop(props, "mirror", text="", icon='MOD_MIRROR', toggle=True)

            if n_pts != n_segs:
                layout.label(text=f"Out of sync ({n_pts}/{n_segs}) — hit refresh", icon='ERROR')

            if n_pts > 0:
                n_total = n_pts + 1
                mirroring = props.mirror and n_pts >= 2
                for i, cp in enumerate(props.control_points):
                    pct = int(round((i + 1) / n_total * 100))
                    mirror_idx = n_pts - 1 - i
                    is_middle = (mirror_idx == i)
                    is_mirrored_slave = mirroring and i > mirror_idx

                    r = layout.row(align=True)
                    if mirroring and not is_middle and not is_mirrored_slave:
                        pct2 = int(round((mirror_idx + 1) / n_total * 100))
                        r.label(text="", icon='LINKED')
                        r.prop(cp, "weight", slider=True, text=f"{pct}% + {pct2}%")
                    elif is_mirrored_slave:
                        r.enabled = False
                        r.label(text="", icon='LINKED')
                        r.prop(cp, "weight", slider=True, text=f"{pct}%")
                    elif mirroring and is_middle:
                        r.label(text="", icon='DECORATE')
                        r.prop(cp, "weight", slider=True, text=f"{pct}% (mid)")
                    else:
                        r.prop(cp, "weight", slider=True, text=f"{pct}%")


# ---------------------------------------------------------------------------
# Adjust Weights sub-panel
# ---------------------------------------------------------------------------

class VIEW3D_PT_wg_adjust(Panel):
    bl_label = "Adjust Weights"
    bl_idname = "VIEW3D_PT_wg_adjust"
    bl_parent_id = "VIEW3D_PT_weight_gradient"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BK Weight Gradient"

    poll = classmethod(_poll_mesh)

    def draw(self, context):
        layout = self.layout
        props = context.scene.weight_gradient
        layout.label(text="Select vertices, set offset, apply:", icon='INFO')
        layout.prop(props, "weight_adjust", slider=True)
        layout.operator("mesh.wg_adjust_weights", icon='DRIVER_TRANSFORM')


# ---------------------------------------------------------------------------
# Storage sub-panel — saved anchors, selections, presets, file I/O
# ---------------------------------------------------------------------------

class VIEW3D_PT_wg_storage(Panel):
    bl_label = "Saved Data & Presets"
    bl_idname = "VIEW3D_PT_wg_storage"
    bl_parent_id = "VIEW3D_PT_weight_gradient"
    bl_options = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BK Weight Gradient"

    poll = classmethod(_poll_mesh)

    def draw(self, context):
        layout = self.layout
        props = context.scene.weight_gradient

        # -- Saved Anchor Sets ----------------------------------------------
        box = layout.box()
        box.label(text="Saved Anchors:", icon='ANCHOR_CENTER')

        grp_row = box.row(align=True)
        grp_row.label(text="Groups:", icon='FILE_FOLDER')
        grp_row.operator("mesh.wg_add_anchor_group", text="", icon='ADD')
        box.template_list(
            "WG_UL_anchor_groups", "",
            props, "saved_anchor_groups",
            props, "active_anchor_group_index",
            rows=2, maxrows=4,
        )

        n_groups = len(props.saved_anchor_groups)
        if n_groups > 0 and 0 <= props.active_anchor_group_index < n_groups:
            active_grp = props.saved_anchor_groups[props.active_anchor_group_index].name
            box.label(text=f"In '{active_grp}':", icon='FILTER')
        else:
            box.label(text="All anchor sets:")
            n_groups = 0

        box.template_list(
            "WG_UL_saved_anchor_sets", "",
            props, "saved_anchor_sets",
            props, "active_anchor_set_index",
            rows=2, maxrows=5,
        )

        row = box.row(align=True)
        row.operator("mesh.wg_save_anchor_set", text="Save", icon='ADD')
        sub = row.row(align=True)
        sub.enabled = len(props.saved_anchor_sets) > 0
        op = sub.operator("mesh.wg_load_anchor_set", text="Load", icon='CHECKMARK')
        op.index = props.active_anchor_set_index
        sub2 = row.row(align=True)
        sub2.enabled = (len(props.saved_anchor_sets) > 0 and n_groups > 0)
        op2 = sub2.operator("mesh.wg_assign_to_group", text="Assign", icon='LINK_BLEND')
        op2.set_index = props.active_anchor_set_index

        # -- Saved Selections -----------------------------------------------
        layout.separator()
        box = layout.box()
        box.label(text="Saved Gradient Vertices:", icon='RESTRICT_SELECT_OFF')

        n_sel_groups = len(props.saved_selection_groups)
        sel_grp_row = box.row(align=True)
        sel_grp_row.label(text="Groups:", icon='FILE_FOLDER')
        sel_grp_row.operator("mesh.wg_add_selection_group", text="", icon='ADD')
        box.template_list(
            "WG_UL_selection_groups", "",
            props, "saved_selection_groups",
            props, "active_selection_group_index",
            rows=2, maxrows=4,
        )

        if n_sel_groups > 0 and 0 <= props.active_selection_group_index < n_sel_groups:
            active_sel_grp = props.saved_selection_groups[props.active_selection_group_index].name
            box.label(text=f"In '{active_sel_grp}':", icon='FILTER')
        else:
            box.label(text="All gradient vertices:")
            n_sel_groups = 0

        box.template_list(
            "WG_UL_saved_selections", "",
            props, "saved_selections",
            props, "active_selection_index",
            rows=2, maxrows=5,
        )

        row = box.row(align=True)
        row.operator("mesh.wg_save_selection", text="Save", icon='ADD')
        sub = row.row(align=True)
        sub.enabled = len(props.saved_selections) > 0
        op = sub.operator("mesh.wg_load_selection", text="Load", icon='CHECKMARK')
        op.index = props.active_selection_index
        sub2 = row.row(align=True)
        sub2.enabled = (len(props.saved_selections) > 0 and n_sel_groups > 0)
        op2 = sub2.operator("mesh.wg_assign_selection_to_group", text="Assign", icon='LINK_BLEND')
        op2.set_index = props.active_selection_index

        # -- Settings Presets -----------------------------------------------
        layout.separator()
        box = layout.box()
        box.label(text="Settings Presets:", icon='PRESET')
        box.template_list(
            "WG_UL_full_presets", "",
            props, "saved_full_presets",
            props, "active_full_preset_index",
            rows=2, maxrows=5,
        )
        row = box.row(align=True)
        row.operator("mesh.wg_save_full_preset", text="Save", icon='ADD')
        sub = row.row(align=True)
        sub.enabled = len(props.saved_full_presets) > 0
        op = sub.operator("mesh.wg_load_full_preset", text="Load", icon='CHECKMARK')
        op.index = props.active_full_preset_index

        # -- Presets File (Export / Import) ---------------------------------
        layout.separator()
        box = layout.box()
        box.label(text="Presets File:", icon='FILE')
        row = box.row(align=True)
        row.operator("mesh.wg_export_presets", text="Export All", icon='EXPORT')
        row.operator("mesh.wg_import_presets", text="Import", icon='IMPORT')


classes = (
    WG_UL_saved_curves,
    WG_UL_saved_selections,
    WG_UL_selection_groups,
    WG_UL_anchor_groups,
    WG_UL_saved_anchor_sets,
    WG_UL_full_presets,
    VIEW3D_PT_weight_gradient,
    VIEW3D_PT_wg_curve,
    VIEW3D_PT_wg_adjust,
    VIEW3D_PT_wg_storage,
)
