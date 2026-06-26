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


# ── Renderer class ────────────────────────────────────────────────────

class Renderer:

    def __init__(self, width, height):
        self.width  = width
        self.height = height
        self._rot_x = 28.0     # isometric default
        self._rot_y = -38.0
        self._view  = None
        self._rebuild_view()

    # ── Rotation ──────────────────────────────────────────────────────

    def add_rotation(self, dx_deg, dy_deg):
        self._rot_x = max(-89.0, min(89.0, self._rot_x + dx_deg))
        self._rot_y += dy_deg
        self._rebuild_view()

    def reset_rotation(self):
        self._rot_x = 28.0
        self._rot_y = -38.0
        self._rebuild_view()

    def _rebuild_view(self):
        self._view = compose(rotation_x(self._rot_x), rotation_y(self._rot_y))

    # ── GL setup ──────────────────────────────────────────────────────

    def setup(self, puzzle_size=5):
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.09, 0.11, 0.17, 1.0)
        self._set_projection(puzzle_size)

    def _set_projection(self, puzzle_size=5):
        aspect = self.width / self.height
        extent = max(4.2, puzzle_size * 0.78)
        proj   = ortho_matrix(
            -extent * aspect,  extent * aspect,
            -extent,            extent,
            -60.0,              60.0,
        )
        glMatrixMode(GL_PROJECTION)
        glLoadMatrixf(to_gl(proj))
        glMatrixMode(GL_MODELVIEW)

    # ── Frame ─────────────────────────────────────────────────────────

    def begin_frame(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(to_gl(self._view))

    # ── Draw all cubes ────────────────────────────────────────────────

    def draw_cubes(self, cubes, picking_mode=False, grid=None):
        for cube in cubes:
            if cube.is_removed:
                continue
            self._draw_cube(cube, picking_mode, grid)

    def _draw_cube(self, cube: Cube, picking_mode: bool, grid):
        # World position = grid_to_world(grid_key) + anim_offset
        if grid is not None:
            wx, wy, wz = grid.grid_to_world(cube.grid_key)
        else:
            # Fallback (shouldn't happen): treat grid_key as world
            wx, wy, wz = (float(v) for v in cube.grid_key)

        wx += cube.anim_offset[0]
        wy += cube.anim_offset[1]
        wz += cube.anim_offset[2]

        model = translation_matrix(wx, wy, wz)
        mv    = self._view @ model

        glPushMatrix()
        glLoadMatrixf(to_gl(mv))

        if picking_mode:
            r, g, b = cube.pick_color
            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            for verts in FACE_QUADS.values():
                for v in verts:
                    glVertex3fv(v)
            glEnd()
        else:
            self._draw_faces(cube)
            self._draw_edges(cube)
            self._draw_arrow(cube)

        glPopMatrix()

    def _draw_faces(self, cube: Cube):
        hover   = cube.hovered
        blocked = cube.is_blocked_flash

        for face, verts in FACE_QUADS.items():
            br, bg, bb = FACE_COLORS[face]
            diff = float(max(0.30, np.dot(FACE_NORMALS[face], _LIGHT)))
            r, g, b = br * diff, bg * diff, bb * diff

            if blocked:
                r = min(1.0, r + 0.55)
                g = max(0.0, g - 0.15)
                b = max(0.0, b - 0.15)
            elif hover:
                r = min(1.0, r + HOVER_BRIGHTEN)
                g = min(1.0, g + HOVER_BRIGHTEN)
                b = min(1.0, b + HOVER_BRIGHTEN)

            glColor3f(r, g, b)
            glBegin(GL_QUADS)
            for v in verts:
                glVertex3fv(v)
            glEnd()

    def _draw_edges(self, cube: Cube):
        if cube.is_blocked_flash:
            glColor3f(0.95, 0.08, 0.08)
            glLineWidth(3.0)
        else:
            glColor3f(0.06, 0.06, 0.08)
            glLineWidth(1.8)
        glBegin(GL_LINES)
        for a, b in _CUBE_EDGES:
            glVertex3fv(a)
            glVertex3fv(b)
        glEnd()
        glLineWidth(1.8)

    def _draw_arrow(self, cube: Cube):
        lines = _arrow_lines(cube.direction)
        if not lines:
            return

        if cube.hovered:
            glColor3f(1.0, 0.92, 0.08)
            glLineWidth(4.0)
        else:
            glColor3f(0.05, 0.05, 0.06)
            glLineWidth(2.2)

        glBegin(GL_LINES)
        for start, end in lines:
            glVertex3fv(start)
            glVertex3fv(end)
        glEnd()
        glLineWidth(1.8)

    # ── Shadow / ground grid ─────────────────────────────────────────

    def draw_ground_grid(self, puzzle_size=5):
        span = puzzle_size // 2 + 2
        y    = -(puzzle_size / 2.0) - 0.72
        glColor4f(0.22, 0.26, 0.36, 0.45)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(-span, span + 1):
            glVertex3f(float(i), y, float(-span))
            glVertex3f(float(i), y, float( span))
            glVertex3f(float(-span), y, float(i))
            glVertex3f(float( span), y, float(i))
        glEnd()
        glLineWidth(1.8)

    # ── Back-buffer colour picking ────────────────────────────────────

    def do_pick_pass(self, cubes, grid=None):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadMatrixf(to_gl(self._view))
        self.draw_cubes(cubes, picking_mode=True, grid=grid)
        glFlush()

    def read_pick_color(self, x, y):
        gl_y = self.height - y - 1
        px   = glReadPixels(x, gl_y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
        if isinstance(px, bytes):
            r, g, b = px[0], px[1], px[2]
        else:
            try:
                r, g, b = px[0][0]
            except (TypeError, IndexError):
                r, g, b = int(px[0]), int(px[1]), int(px[2])
        return (int(r) << 16) | (int(g) << 8) | int(b)