"""
renderer.py  —  All OpenGL rendering.

Pipeline
--------
  Projection  : ortho_matrix()  → glLoadMatrixf(to_gl(...))
  View        : compose(rotation_x, rotation_y) → glLoadMatrixf(to_gl(...))
  Per-cube MV : view_matrix @ translation_matrix(world_pos) → glLoadMatrixf

No raw glRotatef / glTranslatef / glOrtho anywhere.
"""

import numpy as np
from OpenGL.GL import *

from cube import Cube, FACE_COLORS, HOVER_BRIGHTEN, DIRECTION_STEPS
from transform import (
    ortho_matrix, compose, rotation_x, rotation_y,
    translation_matrix, to_gl
)

# ── Cube geometry ────────────────────────────────────────────────────

H = 0.45   # half-extent (small gap between cubes)

FACE_QUADS = {
    'top':    [(-H, H,-H),( H, H,-H),( H, H, H),(-H, H, H)],
    'bottom': [(-H,-H, H),( H,-H, H),( H,-H,-H),(-H,-H,-H)],
    'front':  [(-H,-H, H),( H,-H, H),( H, H, H),(-H, H, H)],
    'back':   [( H,-H,-H),(-H,-H,-H),(-H, H,-H),( H, H,-H)],
    'right':  [( H,-H, H),( H,-H,-H),( H, H,-H),( H, H, H)],
    'left':   [(-H,-H,-H),(-H,-H, H),(-H, H, H),(-H, H,-H)],
}

FACE_NORMALS = {
    'top':    np.array([ 0,  1,  0], dtype=np.float32),
    'bottom': np.array([ 0, -1,  0], dtype=np.float32),
    'front':  np.array([ 0,  0,  1], dtype=np.float32),
    'back':   np.array([ 0,  0, -1], dtype=np.float32),
    'right':  np.array([ 1,  0,  0], dtype=np.float32),
    'left':   np.array([-1,  0,  0], dtype=np.float32),
}

_CUBE_EDGES = [
    ((-H,-H,-H),( H,-H,-H)),(( H,-H,-H),( H,-H, H)),
    (( H,-H, H),(-H,-H, H)),((-H,-H, H),(-H,-H,-H)),
    ((-H, H,-H),( H, H,-H)),(( H, H,-H),( H, H, H)),
    (( H, H, H),(-H, H, H)),((-H, H, H),(-H, H,-H)),
    ((-H,-H,-H),(-H, H,-H)),(( H,-H,-H),( H, H,-H)),
    (( H,-H, H),( H, H, H)),((-H,-H, H),(-H, H, H)),
]

# Key light direction (normalised)
_LIGHT = np.array([0.55, 1.0, 0.65], dtype=np.float32)
_LIGHT /= np.linalg.norm(_LIGHT) 

# ── Arrow geometry ────────────────────────────────────────────────────
# Each arrow pokes straight out of the cube's outward face, ALONG THE
# SAME AXIS the cube will actually fly (see cube.DIRECTION_STEPS /
# transform.direction_vector). This guarantees the arrow you see always
# matches the direction the cube animates away in — previously the
# arrow was drawn on the right face but pointing along a perpendicular
# (cosmetic) axis, which didn't match the real flight direction.

# (axis_index, sign) for each direction — must mirror DIRECTION_STEPS.
_ARROW_AXIS = {
    'right': (0,  1),
    'left':  (0, -1),
    'up':    (1,  1),
    'down':  (1, -1),
    'front': (2,  1),
    'back':  (2, -1),
}

def _arrow_lines(direction):
    axis, sign = _ARROW_AXIS[direction]
    perp = [i for i in range(3) if i != axis][0]   # one perpendicular axis for the barbs

    poke = 0.30   # how far the tip pokes out beyond the cube face
    hw   = 0.11   # barb half-width
    hl   = 0.15   # barb length (measured back along the flight axis from the tip)

    base = [0.0, 0.0, 0.0]
    base[axis] = H * sign                       # sits right on the cube's surface

    tip = [0.0, 0.0, 0.0]
    tip[axis] = (H + poke) * sign                # sticks out along the true flight axis

    barb_root = [0.0, 0.0, 0.0]
    barb_root[axis] = (H + poke - hl) * sign

    b1 = list(barb_root); b1[perp] =  hw
    b2 = list(barb_root); b2[perp] = -hw

    return [
        (tuple(base), tuple(tip)),
        (tuple(b1),   tuple(tip)),
        (tuple(b2),   tuple(tip)),
    ]

