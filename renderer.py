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