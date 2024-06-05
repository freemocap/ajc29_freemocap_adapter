from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Any, Self, Dict, Union, Tuple

import numpy as np

from freemocap_blender_addon.utilities.type_safe_dataclass import TypeSafeDataclass


@dataclass
class Keypoint(TypeSafeDataclass, ABC):
    """
    A Keypoint is a named "key" location on a skeleton, used to define the position of a rigid body or linkage.
    In marker-based motion capture, keypoints could correspond to markers placed on the body.
    In markerless motion capture, keypoints could correspond to a tracked point in the image.
    When a Keypoint is hydrated with data, it becomes a Trajectory.
    """
    name: str


@dataclass
class RigidBodyABC(ABC):
    """
    A RigigBody is a collection of keypoints that are linked together, such that the distance between them is constant.
    """
    parent: Keypoint

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self):
        return self.parent


@dataclass
class SimpleRigidBodyABC(RigidBodyABC):
    """
    A simple rigid body is a RigidBody consisting of Two and Only Two keypoints that are linked together, the distance between them is constant.
    The parent keypoint defines the origin of the rigid body, and the child keypoint is the end of the rigid body.
    The primary axis (+X) of the rigid body is the vector from the parent to the child, the secondary and tertiary axes (+Y, +Z) are undefined (i.e. we have enough information to define the pitch and yaw, but not the roll).
    """
    parent: Keypoint
    child: Keypoint

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self) -> Keypoint:
        return self.parent

    def __post_init__(self):
        if not all(isinstance(keypoint, Keypoint) for keypoint in [self.parent, self.child]):
            raise ValueError("Parent and child keypoints must be instances of Keypoint")
        if self.parent == self.child:
            raise ValueError("Parent and child keypoints must be different")


@dataclass
class CompoundRigidBodyABC(RigidBodyABC):
    """
    A composite rigid body is a collection of keypoints that are linked together, such that the distance between all keypoints is constant.
    The parent keypoint is the origin of the rigid body
    The primary and secondary axes must be defined in the class, and will be used to calculate the orthonormal basis of the rigid body
    """
    parent: Keypoint
    children: List[Keypoint]
    shared_keypoint: Keypoint
    positive_x_direction: Keypoint
    approximate_positive_y_direction: Optional[Keypoint]
    approximate_negative_y_direction: Optional[Keypoint]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self) -> Keypoint:
        return self.parent

    def __post_init__(self):
        if not any(child == self.shared_keypoint for child in self.children):
            raise ValueError(f"Shared keypoint {self.shared_keypoint.name} not found in children {self.children}")
        if not any(child == self.positive_x_direction for child in self.children):
            raise ValueError(
                f"Positive X direction {self.positive_x_direction.name} not found in children {self.children}")
        if self.approximate_positive_y_direction and not any(
                child == self.approximate_positive_y_direction for child in self.children):
            raise ValueError(
                f"Approximate Positive Y direction {self.approximate_positive_y_direction.name} not found in children {self.children}")
        if self.approximate_negative_y_direction and not any(
                child == self.approximate_negative_y_direction for child in self.children):
            raise ValueError(
                f"Approximate Negative Y direction {self.approximate_negative_y_direction.name} not found in children {self.children}")

        if not self.approximate_positive_y_direction and not self.approximate_negative_y_direction:
            raise ValueError(
                "At least one of approximate_positive_y_direction or approximate_negative_y_direction must be defined")

    @property
    def orthonormal_basis(self):
        raise NotImplementedError("TODO - this lol")


@dataclass
class LinkageABC(ABC):
    """
    A simple linkage comprises two RigidBodies that share a common Keypoint.

    The distance from the linked keypoint is fixed relative to the keypoints in the same rigid body,
     but the distances between the unlinked keypoints may change.

     #for now these are all 'universal' (ball) joints. Later we can add different constraints
    """
    parent: RigidBodyABC
    children: [RigidBodyABC]
    # TODO - calculate the linked_point on instantiation rather than defining it manually
    linked_keypoints: [Keypoint]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self) -> Keypoint:
        return self.parent.root

    def __post_init__(self):
        for body in [self.parent, self.children]:
            for keypoint in self.linked_keypoints:
                if isinstance(body, SimpleRigidBodyABC):
                    if keypoint not in [body.parent, body.child]:
                        raise ValueError(f"Common keypoint {keypoint.name} not found in body {body}")
                elif isinstance(body, CompoundRigidBodyABC):
                    if keypoint not in [body.parent] + body.children:
                        raise ValueError(f"Common keypoint {keypoint.name} not found in body {body}")
                else:
                    raise ValueError(f"Body {body} is not a valid rigid body type")

    def __str__(self) -> str:
        out_str = super().__str__()
        out_str += "\n\t".join(f"Common Keypoints: {self.linked_keypoints}\n")
        return out_str


class ChainABC(ABC):
    """
    A Chain is a set of linkages that are connected via shared RigidBodies.
    """
    parent: LinkageABC
    children: List[LinkageABC]
    # TODO - calculate the linked_point on instanciation rather than defining it manually
    shared_bodies: List[RigidBodyABC]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self) -> Keypoint:
        # Chain -> Linkage -> RigidBody -> Keypoint
        return self.parent.root

    def __post_init__(self):
        for body in self.shared_bodies:
            if not any(body == linkage.parent for linkage in self.children):
                raise ValueError(f"Shared body {body.name} not found in children {self.children}")


class SkeletonABC(ABC):
    """
    A Skeleton is composed of chains with connecting KeyPoints.
    """
    parent: ChainABC
    children: List[ChainABC]

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def root(self) -> Keypoint:
        # Skeleton -> Chain -> Linkage -> RigidBody -> Keypoint
        return self.parent.root


### Abstract Enum Classes & Auxilliary Classes ###
TrackerName = str
Mapping = Union[List[TrackerName], Dict[TrackerName, float], Dict[Keypoint, Tuple[float, float, float]]]
@dataclass
class KeypointMapping(TypeSafeDataclass):
    mapping: Mapping  # map to local offset from parent keypoint
    weights: Optional[List[float]] = None

    def __post_init__(self):
        if isinstance(self.source_keypoints, dict):
            self.source_keypoints = list(self.source_keypoints.keys())
            self.weights = list(self.source_keypoints.values())

        if self.weights is None:
            self.weights = [1 / len(self.source_keypoints)] * len(self.source_keypoints)

        if len(self.source_keypoints) != len(self.weights):
            raise ValueError("The number of parent keypoints must match the number of weights")

        if np.sum(self.weights) != 1:
            raise ValueError("The sum of the weights must be 1")


class KeypointsEnum(Enum):
    """An enumeration of Keypoint instances, ensuring each member is a Keypoint.

    Methods
    -------
    __new__(cls, *args, **kwargs):
        Creates a new Keypoint instance with the enum member name as the Keypoint name.
    _generate_next_value_(name, start, count, last_values):
        Generates the next value for the auto-assigned enum members.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @classmethod
    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        obj = object.__new__(cls)
        obj._value_ = Keypoint(name=args[1])
        return obj

    @staticmethod
    def _generate_next_value_(name, start, count, last_values) -> str:
        return name

    def __str__(self) -> str:
        out_str = f"{self.name}: \n {self.value}"
        return out_str