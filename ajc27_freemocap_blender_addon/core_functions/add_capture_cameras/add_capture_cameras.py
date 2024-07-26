import bpy
import toml
import os
import math
from mathutils import Vector, Matrix, Euler

def add_capture_cameras(
    recording_folder: str='',
    skeleton_transform: dict={},
) -> None:
    calibration_file_path = None

    print('Skeleton transform:', skeleton_transform)
    print('Translation Vector:', skeleton_transform['center_reference_point'].tolist())
    print('Rotation Matrix:', skeleton_transform['rotation_matrix'].tolist())
    print('Rotation Matrix row1:', skeleton_transform['rotation_matrix'].tolist()[0])
    print('Rotation Matrix row2:', skeleton_transform['rotation_matrix'].tolist()[1])
    print('Rotation Matrix row3:', skeleton_transform['rotation_matrix'].tolist()[2])


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
    camera_0_translation = Vector([
        skeleton_transform['center_reference_point'][0] * -1,
        skeleton_transform['center_reference_point'][1] * -1,
        skeleton_transform['center_reference_point'][2] * -1,
    ])
    camera_0_rotation_matrix = Matrix(skeleton_transform['rotation_matrix'].tolist())

    camera_0_rotation = Vector([
        -cameras_dict['cam_0']['rotation'][0],
        -cameras_dict['cam_0']['rotation'][1],
        -cameras_dict['cam_0']['rotation'][2],
    ])

    # Add the cameras to the scene
    for key in cameras_dict.keys():
        if key == 'cam_0':
            bpy.ops.object.camera_add(
                location=camera_0_translation,                 
                rotation=camera_0_rotation
            )
            cam_0_world_matrix = bpy.context.object.matrix_world
        else:
            # Get the relative location and rotation of the camera
            # camera_relative_location = (
            #     cameras_dict[key]['translation'][0] / 1000 * -1,
            #     cameras_dict[key]['translation'][1] / 1000,
            #     cameras_dict[key]['translation'][2] / 1000,
            # )
            camera_relative_location = (
                cameras_dict[key]['translation'][0] / 1000 * -1,
                cameras_dict[key]['translation'][1] / 1000 * -1,
                cameras_dict[key]['translation'][2] / 1000,
            )
            print('camera_relative_location:', camera_relative_location)
            camera_relative_rotation = (
                cameras_dict[key]['rotation'][0],
                cameras_dict[key]['rotation'][1],
                cameras_dict[key]['rotation'][2],
            )
            
            camera_rotation_matrix = Euler(camera_relative_rotation, 'XYZ').to_matrix().to_4x4()

            # Calculate the world matrix of the camera based on cam_0
            camera_world_matrix = (
                cam_0_world_matrix
                @ Matrix.Translation(camera_relative_location)
                @ camera_rotation_matrix
            )
            
            bpy.ops.object.camera_add()
            bpy.context.object.location = camera_world_matrix.translation
            # bpy.context.object.rotation_euler = camera_world_matrix.to_euler()

        # Set the name of the camera
        bpy.context.object.name = key
        # Show the name in the viewport
        bpy.context.object.show_name = True
        # Change the camera focal length
        bpy.context.object.data.lens = 25
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
