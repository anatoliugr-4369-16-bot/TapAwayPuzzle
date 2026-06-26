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
    # ── Tap ──

    def try_tap(self, cube: Cube) -> bool:
        """
        Attempt to launch cube.
        Returns True on success (path was clear), False if blocked.
        Blocked cubes get a red flash; no other state change.
        """
        if self.state != 'playing':
            return False
        if cube.is_animating or cube.is_removed:
            return False

        if self.grid.is_path_clear(cube):
            self.grid.launch_cube(cube)
            self.taps  += 1
            self.score += 10
            return True
        else:
            cube.blocked_timer = 0.55   # red flash duration (seconds)
            return False    
    # ── Per-frame update ─────────────────────────────────────────────

    def update(self, dt: float):
        if self.state != 'playing':
            return

        self.grid.update(dt)

        # Only evaluate end-conditions when nothing is flying
        if self.grid.in_flight_count() > 0:
            return

        if self.grid.active_count() == 0:
            self.state  = 'won'
            self.score += 200
        elif self.grid.is_stuck():
            self.state  = 'stuck'
    # ── Properties ──────────────────────────────────────────────────

    @property
    def is_won(self):
        return self.state == 'won'

    @property
    def is_stuck(self):
        return self.state == 'stuck'            