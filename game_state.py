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
# ── Puzzle management ───────────────────────────────────────────

    def start_puzzle(self, size: int = 5):
        self.puzzle_size = size
        self.state       = 'playing'
        self.score       = 0
        self.taps        = 0
        self.grid.generate(size=size)

    def restart(self):
        """
        Restore the EXACT same puzzle (same arrows, same layout).
        Does NOT re-randomise — proper restart like the real game.
        """
        self.state  = 'playing'
        self.score  = 0
        self.taps   = 0
        self.grid.restart()

    def shuffle(self):
        """Reassign arrows to break a stuck state (costs 50 pts)."""
        if self.state not in ('playing', 'stuck'):
            return
        self.grid.shuffle_directions()
        self.score = max(0, self.score - 50)
        self.state = 'playing'