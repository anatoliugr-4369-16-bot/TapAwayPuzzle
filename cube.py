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