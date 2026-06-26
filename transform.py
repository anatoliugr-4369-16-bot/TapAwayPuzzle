"""
transform.py  —  Matrix math for the entire render pipeline.
Column-major 4×4 (OpenGL convention).  NO raw gl*f calls anywhere else.
"""

import math
import numpy as np
s

def identity():
    return np.eye(4, dtype=np.float32)


def translation_matrix(tx, ty, tz):
    m = identity()
    m[0, 3] = tx
    m[1, 3] = ty
    m[2, 3] = tz
    return m


def scale_matrix(sx, sy, sz):
    m = identity()
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def rotation_x(angle_deg):
    a = math.radians(angle_deg)
    m = identity()
    m[1, 1] =  math.cos(a); m[1, 2] = -math.sin(a)
    m[2, 1] =  math.sin(a); m[2, 2] =  math.cos(a)
    return m


def rotation_y(angle_deg):
    a = math.radians(angle_deg)
    m = identity()
    m[0, 0] =  math.cos(a); m[0, 2] =  math.sin(a)
    m[2, 0] = -math.sin(a); m[2, 2] =  math.cos(a)
    return m


def rotation_z(angle_deg):
    a = math.radians(angle_deg)
    m = identity()
    m[0, 0] =  math.cos(a); m[0, 1] = -math.sin(a)
    m[1, 0] =  math.sin(a); m[1, 1] =  math.cos(a)
    return m


def compose(*matrices):
    """Left-to-right multiply: compose(A,B,C) = A @ B @ C"""
    result = identity()
    for m in matrices:
        result = result @ m
    return result


def ortho_matrix(left, right, bottom, top, near, far):
    """Orthographic projection — equivalent to glOrtho, loaded via glLoadMatrixf."""
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] =  2.0 / (right - left)
    m[1, 1] =  2.0 / (top   - bottom)
    m[2, 2] = -2.0 / (far   - near)
    m[0, 3] = -(right + left)   / (right - left)
    m[1, 3] = -(top   + bottom) / (top   - bottom)
    m[2, 3] = -(far   + near)   / (far   - near)
    m[3, 3] =  1.0
    return m


def to_gl(m):
    """Column-major flat float32 array for glLoadMatrixf / glMultMatrixf."""
    return m.T.flatten().astype(np.float32)


# Direction unit vectors (for animation path)
_DIR_VECS = {
    'right': np.array([ 1,  0,  0], dtype=np.float32),
    'left':  np.array([-1,  0,  0], dtype=np.float32),
    'up':    np.array([ 0,  1,  0], dtype=np.float32),
    'down':  np.array([ 0, -1,  0], dtype=np.float32),
    'front': np.array([ 0,  0,  1], dtype=np.float32),
    'back':  np.array([ 0,  0, -1], dtype=np.float32),
}

def direction_vector(name):
    return _DIR_VECS[name].copy()
