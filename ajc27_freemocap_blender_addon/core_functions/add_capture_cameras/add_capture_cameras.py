import bpy
import toml
import os
import math
from mathutils import Vector

def add_capture_cameras(
    recording_folder: str='',
) -> None:
    calibration_file_path = None

    # Find the calibration file in the recording folder
    for file in os.listdir(recording_folder):
        if file.endswith('.toml'):
            calibration_file_path = os.path.join(recording_folder, file)
    
    # If there is no calibration file, return
    if calibration_file_path is None:
        print('No calibration file found in the recording folder')
        return

    # Load the TOML file
    with open(calibration_file_path, 'r') as file:
        data = toml.load(file)

    # Extract camera information into a dictionary
    cameras_dict = {}
    for key, value in data.items():
        if key.startswith('cam_'):
            cameras_dict[key] = value

    # Find the data origin empty object to parent the cameras
    for obj in bpy.data.objects:
        # If the object name end with '_origin', it is the data origin
        if obj.name.endswith('_origin'):
            data_origin = obj
            break

    # Create a new empty object to hold the cameras
    bpy.ops.object.empty_add(type='ARROWS',
                             align='WORLD',
                             location=(0, 0, 0),
                             scale=(0.1, 0.1, 0.1)
    )
    cameras_parent = bpy.context.active_object
    cameras_parent.name = 'capture_cameras_parent'
    cameras_parent.parent = data_origin
    # Hide the camera parent in viewport
    cameras_parent.hide_set(True)

    # Set the scene resolution equal to cam_0 resolution
    bpy.context.scene.render.resolution_x = cameras_dict['cam_0']['size'][0]
    bpy.context.scene.render.resolution_y = cameras_dict['cam_0']['size'][1]

    # Get camera zero translation and rotation
    camera_zero_translation = Vector([-2.53, -5.47, 1.13])
    camera_zero_rotation = Vector([math.radians(85.099),
                                   math.radians(2.1712),
                                   math.radians(-32.809)]) #29

    # Add the cameras to the scene
    for key in cameras_dict.keys():
        if key == 'cam_0':
            bpy.ops.object.camera_add(
                location = camera_zero_translation,                 
                rotation = camera_zero_rotation
                           + Vector([
                                cameras_dict[key]['rotation'][0],
                                cameras_dict[key]['rotation'][1],
                                cameras_dict[key]['rotation'][2],
                           ])
            )
        else:
            bpy.ops.object.camera_add(
                location = camera_zero_translation
                           + Vector([
                                cameras_dict[key]['translation'][0] / 1000 * -1,
                                cameras_dict[key]['translation'][1] / 1000,
                                cameras_dict[key]['translation'][2] / 1000,
                            ]),
                rotation = camera_zero_rotation
                           + Vector([
                                cameras_dict[key]['rotation'][0],
                                cameras_dict[key]['rotation'][1],
                                cameras_dict[key]['rotation'][2],
                           ])
            )

        # Set the name of the camera
        bpy.context.object.name = key
        # Parent the camera to the cameras parent
        bpy.context.object.parent = cameras_parent

        # Add the correspondent capture video to the background of each camera
        # Get the path of the capture video
        capture_video_path = (
            recording_folder
            + '/synchronized_videos/'
            + cameras_dict[key]['name']
            + '.mp4'
        )

        # Load the capture video
        capture_video = bpy.data.movieclips.load(capture_video_path)

        # Add the capture video as a background image
        camera_data = bpy.data.objects[key].data
        camera_background = camera_data.background_images.new()
        camera_background.source = 'MOVIE_CLIP'
        camera_background.clip = capture_video
        camera_background.alpha = 1
       
        camera_data.show_background_images = True

    return
