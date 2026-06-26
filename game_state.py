"""
game_state.py  —  Game lifecycle: tap logic, state machine, score.

States
------
  'playing'  : normal gameplay
  'won'      : all cubes removed
  'stuck'    : cubes remain but none can move (no animation in flight)
"""

from grid import Grid
from cube import Cube


class GameState:

    def __init__(self):
        self.grid         = Grid()
        self.state        = 'playing'
        self.score        = 0
        self.puzzle_size  = 5
        self.taps         = 0