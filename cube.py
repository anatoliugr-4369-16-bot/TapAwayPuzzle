"""
cube.py  —  Cube entity.

grid_key  : (int,int,int)  0-based grid index — fixed, never changes.
anim_offset : world-space displacement added during fly-away animation.
The Renderer converts grid_key => world position at draw time.
"""


import numpy as np
from transform import direction_vector

ANIM_SPEED      = 7.0    # world units per second
REMOVE_DISTANCE = 20.0   # cube discarded after travelling this far

DIRECTION_STEPS = {
    'right': ( 1,  0,  0),
    'left':  (-1,  0,  0),
    'up':    ( 0,  1,  0),
    'down':  ( 0, -1,  0),
    'front': ( 0,  0,  1),
    'back':  ( 0,  0, -1),
}
FACE_COLORS = {
    'top':    (0.97, 0.84, 0.38),
    'bottom': (0.48, 0.36, 0.18),
    'front':  (0.52, 0.80, 0.97),
    'back':   (0.22, 0.48, 0.76),
    'right':  (0.92, 0.54, 0.32),
    'left':   (0.68, 0.33, 0.18),
}
HOVER_BRIGHTEN = 0.20

class Cube:
    def __init__(self, grid_key: tuple, direction: str, pick_id: int):
        self.grid_key      = grid_key       # (gx,gy,gz)  int tuple
        self.direction     = direction
        self.pick_id       = pick_id

        r = ((pick_id >> 16) & 0xFF) / 255.0
        g = ((pick_id >>  8) & 0xFF) / 255.0
        b = ( pick_id        & 0xFF) / 255.0
        self.pick_color    = (r, g, b)

        self.is_animating  = False
        self.is_removed    = False
        self.anim_offset   = np.zeros(3, dtype=np.float32)
        self.hovered       = False
        self.blocked_timer = 0.0

    def update(self, dt: float) -> bool:
        """Advance animation / timers.  Returns True when cube finishes flying."""
        if self.blocked_timer > 0:
            self.blocked_timer = max(0.0, self.blocked_timer - dt)

        if not self.is_animating or self.is_removed:
            return False

        dv = direction_vector(self.direction)
        self.anim_offset += dv * ANIM_SPEED * dt

        if float(np.linalg.norm(self.anim_offset)) >= REMOVE_DISTANCE:
            self.is_removed = True
            return True
        return False

    @property
    def is_blocked_flash(self):
        return self.blocked_timer > 0.0

    def __repr__(self):
        return f"Cube(key={self.grid_key}, dir={self.direction})"