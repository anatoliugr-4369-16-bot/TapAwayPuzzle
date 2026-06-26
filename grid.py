"""
grid.py  —  3-D occupancy grid, puzzle generation, and path-clear logic.

Coordinate system
-----------------
  Grid space : integer (gx, gy, gz) in [0, size-1]³.
               Used for ALL occupancy lookups and path walks.
  World space: derived at render time:
                 wx = gx - half,  wy = gy - half,  wz = gz - half
               (half = (size-1)/2)

filled_set  : set of (gx,gy,gz)  — every solid cell (outer + interior).
              A cell is REMOVED from filled_set when its cube is launched,
              so subsequent path checks treat that cell as empty — exactly
              matching Tap Away's rule where animating cubes don't block.

occupancy   : dict (gx,gy,gz) -> Cube  — outer-shell active cubes only.
              Also cleared on launch.

Path-clear rule (verbatim Tap Away)
------------------------------------
  Step from (cube.grid_key + direction_step) outward, one cell at a time.
    • Cell NOT in filled_set  → we left the block  → CLEAR (return True)
    • Cell IS  in filled_set  → solid obstruction  → BLOCKED (return False)
"""

import random
from cube import Cube, DIRECTION_STEPS

ALL_DIRECTIONS = list(DIRECTION_STEPS.keys())


# ── Direction assignment ────────────────────────────────────────────

def _assign_direction(gx, gy, gz, size):
    """
    Assign a random direction from all 6 options.
    Corner/edge cubes on the outer shell get a slight outward bias (60%),
    creating a mix of immediately tappable and blocked cubes that matches
    the real Tap Away game.
    """
    half = (size - 1) / 2.0
    scores = {
        'right': gx - half,  'left':  half - gx,
        'up':    gy - half,  'down':  half - gy,
        'front': gz - half,  'back':  half - gz,
    }
    best = max(scores.values())
    outward = [d for d, s in scores.items() if abs(s - best) < 0.01]

    # 55% chance of outward direction (solvable bias), 45% fully random
    if random.random() < 0.55:
        return random.choice(outward)
    else:
        return random.choice(ALL_DIRECTIONS)


# ── Grid ────────────────────────────────────────────────────────────

class Grid:

    def __init__(self):
        self.size        : int               = 5
        self.cubes       : list[Cube]        = []
        self.occupancy   : dict[tuple, Cube] = {}
        self.filled_set  : set[tuple]        = set()
        self._next_pick  : int               = 1
        # Snapshot for restart (grid_key → direction)
        self._initial_dirs : dict[tuple, str] = {}

    # ── Generation ─────────────────────────────────────────────────

    def generate(self, size: int = 5):
        self.size = size
        self._reset_containers()

        # Fill solid block
        for gx in range(size):
            for gy in range(size):
                for gz in range(size):
                    self.filled_set.add((gx, gy, gz))

        # Create outer-shell cubes
        for key in sorted(self.filled_set):
            if self._is_outer(key):
                gx, gy, gz = key
                d = _assign_direction(gx, gy, gz, size)
                self._initial_dirs[key] = d
                self._make_cube(key, d)

    def restart(self):
        """Restore the exact puzzle that was generated (same arrows)."""
        saved_dirs = dict(self._initial_dirs)   # preserve before clearing
        self.cubes.clear()
        self.occupancy.clear()
        self.filled_set.clear()
        self._next_pick = 1
        self._initial_dirs = saved_dirs         # restore

        for gx in range(self.size):
            for gy in range(self.size):
                for gz in range(self.size):
                    self.filled_set.add((gx, gy, gz))

        for key in sorted(self.filled_set):
            if self._is_outer(key):
                d = self._initial_dirs.get(key,
                        _assign_direction(*key, self.size))
                self._make_cube(key, d)

    def _reset_containers(self):
        self.cubes.clear()
        self.occupancy.clear()
        self.filled_set.clear()
        self._initial_dirs.clear()
        self._next_pick = 1

    def _is_outer(self, key):
        gx, gy, gz = key
        for dx, dy, dz in DIRECTION_STEPS.values():
            if (gx+dx, gy+dy, gz+dz) not in self.filled_set:
                return True
        return False

    def _make_cube(self, key, direction):
        c = Cube(grid_key=key, direction=direction, pick_id=self._next_pick)
        self._next_pick += 1
        self.cubes.append(c)
        self.occupancy[key] = c

    # ── World-space helpers ─────────────────────────────────────────

    def grid_to_world(self, key):
        """Convert grid_key → centred world position (float tuple)."""
        half = (self.size - 1) / 2.0
        gx, gy, gz = key
        return (gx - half, gy - half, gz - half)

    # ── Path-clear check ────────────────────────────────────────────

    def is_path_clear(self, cube: Cube) -> bool:
        """
        Walk from cube.grid_key outward in the arrow direction.
        Returns True iff we exit filled_set without hitting any solid cell.
        Cells launched (animating) are already removed from filled_set.
        """
        dx, dy, dz = DIRECTION_STEPS[cube.direction]
        gx, gy, gz = cube.grid_key

        for _ in range(self.size + 2):
            gx += dx
            gy += dy
            gz += dz
            # Outside the bounding box → exited the structure → CLEAR
            if not (0 <= gx < self.size and
                    0 <= gy < self.size and
                    0 <= gz < self.size):
                return True
            # Inside bounding box AND cell is solid → BLOCKED
            if (gx, gy, gz) in self.filled_set:
                return False
            # Inside bounding box but cell is empty (previously launched) → keep walking
        return True  # walked off the grid

    # ── Launch ─────────────────────────────────────────────────────

    def launch_cube(self, cube: Cube):
        """
        Erase cube from occupancy and filled_set, then start fly-away.
        Removing from filled_set makes the old cell transparent for future
        path checks — this is the key mechanism that makes the puzzle solvable.
        """
        key = cube.grid_key
        self.occupancy.pop(key, None)
        self.filled_set.discard(key)
        cube.is_animating = True

    # ── Stuck / shuffle ────────────────────────────────────────────

    def any_move_available(self) -> bool:
        return any(
            self.is_path_clear(c)
            for c in self.cubes
            if not c.is_removed and not c.is_animating
        )

    def is_stuck(self) -> bool:
        active = [c for c in self.cubes
                  if not c.is_removed and not c.is_animating]
        return bool(active) and not self.any_move_available()

    def shuffle_directions(self):
        """Re-assign arrows so at least one cube can move."""
        active = [c for c in self.cubes
                  if not c.is_removed and not c.is_animating]
        if not active:
            return
        for cube in active:
            gx, gy, gz = cube.grid_key
            cube.direction = _assign_direction(gx, gy, gz, self.size)
        # Guarantee at least one move exists
        if not self.any_move_available():
            for cube in active:
                for d in ALL_DIRECTIONS:
                    cube.direction = d
                    if self.is_path_clear(cube):
                        return

    # ── Per-frame update ───────────────────────────────────────────

    def update(self, dt: float):
        for c in self.cubes:
            c.update(dt)

    # ── Queries ────────────────────────────────────────────────────

    def cube_by_pick_id(self, pick_id: int):
        for c in self.cubes:
            if c.pick_id == pick_id and not c.is_removed:
                return c
        return None

    def active_count(self) -> int:
        return sum(1 for c in self.cubes if not c.is_removed)

    def in_flight_count(self) -> int:
        return sum(1 for c in self.cubes if c.is_animating and not c.is_removed)

    def all_active_cubes(self):
        return [c for c in self.cubes if not c.is_removed]
