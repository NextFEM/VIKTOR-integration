import numpy as np
import math
import viktor as vkt
from viktor.geometry import rotation_matrix
def _generate_transformation_matrix(self) -> np.ndarray:
    """
    The extrusion is drawn in the +z direction, with the profile in the xy plane.
    This method calculates the necessary transformation matrix to rotate the extrusion in the right direction,
    preserving section local axes.
    """

    xax = (1, 0, 0)
    yax = (0, 1, 0)
    zax = (0, 0, 1)

    [target_x, target_y, target_z] = np.array(tuple(self.line.end_point)) - np.array(tuple(self.line.start_point))

    # choose arbitary local axes for the target line
    x_loc = np.array([target_x, target_y, target_z])
    x_loc = x_loc / np.linalg.norm(x_loc)
    if np.linalg.norm(np.array([target_x, target_y])) <= 1e-6:
        y_loc = np.array(yax)
    else:
        y_loc = np.cross(np.array(zax), x_loc)
        y_loc = y_loc / np.linalg.norm(y_loc)
    z_loc = np.cross(x_loc, y_loc)

    # map local ZXY to global XYZ, using target line local axes
    rot0 = np.array([
        [y_loc[0], z_loc[0], x_loc[0], 0],
        [y_loc[1], z_loc[1], x_loc[1], 0],
        [y_loc[2], z_loc[2], x_loc[2], 0],
        [0, 0, 0, 1]])

    # Apply the profile rotation around Z-axis
    rot1 = rotation_matrix(math.radians(self._profile_rotation), zax)

    transformation = rot0 @ rot1
    transformation[0:3, 3] = tuple(self.line.start_point)

    return transformation
# patch _generate_transformation_matrix on the Extrusion class
vkt.Extrusion._generate_transformation_matrix = _generate_transformation_matrix