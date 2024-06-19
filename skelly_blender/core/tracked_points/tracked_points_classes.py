from dataclasses import dataclass, field
from typing import List

import numpy as np

from skelly_blender.core.custom_type_hints import TrackedPointName
from skelly_blender.core.skeleton_model.abstract_base_classes.trajectory_abc import Trajectory
from skelly_blender.core.tracked_points.data_component_types import DataComponentTypes
from skelly_blender.core.tracked_points.tracker_source_types import TrackerSourceType
from skelly_blender.core.utility_classes.type_safe_dataclass import TypeSafeDataclass


@dataclass
class GenericTrackedPoints(TypeSafeDataclass):
    trajectory_data: np.ndarray
    trajectory_names: List[TrackedPointName]
    dimension_names: List[str]
    tracker_source: TrackerSourceType
    component_type: DataComponentTypes = field(default=DataComponentTypes.BODY)

    @property
    def number_of_frames(self):
        return self.trajectory_data.shape[0]

    @property
    def number_of_trajectories(self):
        return self.trajectory_data.shape[1]

    def __post_init__(self):
        if not len(self.trajectory_data.shape) == 3:
            raise ValueError("Data shape should be (frame, trajectory, xyz)")
        if not self.trajectory_data.shape[2] == 3:
            raise ValueError("Trajectory data should be 3D (xyz)")
        if not self.number_of_trajectories == len(self.trajectory_names):
            raise ValueError(
                f"Data frame shape {self.trajectory_data.shape} does not match trajectory names length {len(self.trajectory_names)}")

    def map_to_keypoints(self) -> KeypointTrajectories:
        print("Mapping TrackedPoints to KeypointsTrajectories....")
        mapping = get_mapping(component_type=self.component_type,
                              tracker_source=self.tracker_source)
        keypoint_trajectories = {
            keypoint_name.lower(): Trajectory(name=keypoint_name.lower(),
                                              trajectory_data=mapping.value.calculate_trajectory(
                                                          data=self.trajectory_data,
                                                          names=self.trajectory_names))
            for keypoint_name, mapping in mapping.__members__.items()}
        return keypoint_trajectories


class BodyTrackedPoints(GenericTrackedPoints):
    @classmethod
    def create(cls,
               trajectory_data: np.ndarray,
               tracker_source: TrackerSourceType,
               ):
        return cls(trajectory_data=trajectory_data,
                   trajectory_names=get_keypoint_names(component_type=DataComponentTypes.BODY,
                                                       tracker_source=tracker_source),
                   dimension_names=FRAME_TRAJECTORY_XYZ,
                   tracker_source=tracker_source
                   )


class FaceTrackedPoints(GenericTrackedPoints):
    @classmethod
    def create(cls,
               data: np.ndarray,
               tracker_source: TrackerSourceType):
        return cls(trajectory_data=data,
                   trajectory_names=get_keypoint_names(component_type=DataComponentTypes.FACE,
                                                       tracker_source=tracker_source),
                   dimension_names=FRAME_TRAJECTORY_XYZ,
                   tracker_source=tracker_source
                   )


class HandTrackedPoints(GenericTrackedPoints):
    @classmethod
    def create(cls,
               data: np.ndarray,
               tracker_source: TrackerSourceType,
               component_type: DataComponentTypes):
        return cls(trajectory_data=data,
                   trajectory_names=get_keypoint_names(component_type=component_type,
                                                       tracker_source=tracker_source),
                   dimension_names=FRAME_TRAJECTORY_XYZ,
                   tracker_source=tracker_source
                   )


@dataclass
class HandsData(TypeSafeDataclass):
    right: HandTrackedPoints
    left: HandTrackedPoints

    @classmethod
    def create(cls,
               npy_paths: HandsNpyPaths,
               tracker_source: TrackerSourceType):
        return cls(right=HandTrackedPoints.create(data=np.load(npy_paths.right),
                                                  tracker_source=tracker_source,
                                                  component_type=DataComponentTypes.RIGHT_HAND),
                   left=HandTrackedPoints.create(data=np.load(npy_paths.left),
                                                 tracker_source=tracker_source,
                                                 component_type=DataComponentTypes.LEFT_HAND)
                   )