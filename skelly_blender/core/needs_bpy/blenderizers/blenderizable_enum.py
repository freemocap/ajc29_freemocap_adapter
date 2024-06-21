from enum import Enum

from skelly_blender.core.needs_bpy.blender_type_hints import BlenderizedName
from skelly_blender.core.needs_bpy.blenderizers.blenderize_name import blenderize_name


class BlenderizableEnum(Enum):
    def blenderize(self) -> BlenderizedName:
        return blenderize_name(self.name)


