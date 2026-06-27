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