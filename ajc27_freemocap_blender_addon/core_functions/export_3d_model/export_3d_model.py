import bpy
from pathlib import Path
from bpy_extras.io_utils import axis_conversion

from .fbx import export_fbx_bin

def export_3d_model(
    extension: str='fbx',
    export_folder: str='',
    target_platform: str='default',
) -> None:

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # Select only the rig and the body_mesh.
    for capture_object in bpy.data.objects:
        if capture_object.type == "ARMATURE":
            # Save the original rig name to restore it after the export
            rig_original_name = capture_object.name
            # Rename the rig if its name is different from root
            if capture_object.name != "root":
                capture_object.name = "root"

            # Select the rig                
            capture_object.select_set(True)

    # Select the mesh
    bpy.data.objects['skelly_mesh'].select_set(True)

    if extension == "fbx":

        # Define the export parameters dictionary
        export_parameters = {
            'filepath':export_folder + '/' + Path(export_folder).name + '.fbx',
            'use_selection':True,
            'use_visible':False,
            'use_active_collection':False,
            'global_scale':1.0,
            'apply_unit_scale':True,
            'apply_scale_options':'FBX_SCALE_NONE',
            'use_space_transform':True,
            'bake_space_transform':False,
            'object_types':{'ARMATURE', 'MESH', 'EMPTY'},
            'use_mesh_modifiers':True,
            'use_mesh_modifiers_render':True,
            'mesh_smooth_type':'FACE',
            'colors_type':'SRGB',
            'prioritize_active_color':False,
            'use_subsurf':False,
            'use_mesh_edges':False,
            'use_tspace':False,
            'use_triangles':False,
            'use_custom_props':False,
            'add_leaf_bones':False,
            'primary_bone_axis':'Y',
            'secondary_bone_axis':'X',
            'use_armature_deform_only':False,
            'armature_nodetype':'NULL',
            'bake_anim':True,
            'bake_anim_use_all_bones':True,
            'bake_anim_use_nla_strips':False,
            'bake_anim_use_all_actions':False,
            'bake_anim_force_startend_keying':True,
            'bake_anim_step':1.0,
            'bake_anim_simplify_factor':0.0,
            'path_mode':'AUTO',
            'embed_textures':False,
            'batch_mode':'OFF',
            'use_batch_own_dir':True,
            'use_metadata':True,
            'axis_forward':'Y',
            'axis_up':'Z'
        }

        export_parameters["global_matrix"] = (
            axis_conversion(
                to_forward=export_parameters['axis_forward'],
                to_up=export_parameters['axis_up'],
            ).to_4x4()
        )

        # Simulate the FBX Export Operator Class
        self = type(
            'FMCExportFBX',
            (object,),
            {'report': print("error")}
        )

        # Export the FBX file
        export_fbx_bin.save(self,
                            bpy.context,
                            target_platform,
                            **export_parameters,
        )

    # Restore the name of the rig object
    for capture_object in bpy.data.objects:
        if capture_object.type == "ARMATURE":
            # Restore the original rig name
            capture_object.name = rig_original_name
