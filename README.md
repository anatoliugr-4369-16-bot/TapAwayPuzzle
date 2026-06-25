# Tap Away — Orthographic Puzzle Game 

## Overview

A 3D grid-based puzzle game rendered with **orthographic parallel projection**.
Only the **outer shell** of the block is rendered. Each cube has a directional arrow.
Click a cube to launch it — only if its path in the arrow direction is completely clear.

---

## File Structure

| File              | Responsibility                                                |
| ----------------- | ------------------------------------------------------------- |
| `main.py`         | Window, game loop, 2D HUD overlay                             |
| `renderer.py`     | All OpenGL — uses transform.py matrices via `glLoadMatrixf`   |
| `cube.py`         | Cube entity, animation, blocked-flash state                   |
| `grid.py`         | 3D occupancy, outer-shell generation, path-clear check        |
| `game_state.py`   | Tap logic, win detection, score                               |
| `transform.py`    | Matrix library: rotation, translation, ortho projection       |
| `inputHandler.py` | Mouse input: drag-to-rotate, clickdisambiguation(drag vs tap) |

---

## How to Run

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
python main.py
```

---

## Controls

| Input            | Action                             |
| ---------------- | ---------------------------------- |
| **Click** a cube | Launch it (if path is clear)       |
| **Drag**         | Rotate the block                   |
| **5 / 6 / 7**    | New puzzle (5×5×5 / 6×6×6 / 7×7×7) |
| **R**            | Restart current puzzle             |
| **ESC**          | Quit                               |

---

## Architecture Highlights

### Matrix Pipeline (transform.py → renderer.py)

- `rotation_x`, `rotation_y` compose the view matrix
- `ortho_matrix()` builds the projection — both loaded via `glLoadMatrixf(to_gl(...))`
- Per-cube model matrix (translation) multiplied: `mv = view_matrix @ cube.model_matrix()`
- Zero raw `glRotatef` / `glTranslatef` in the render hot path

### Outer-Shell Generation (grid.py)

- Fills an NxNxN grid, marks cells as `filled_set`
- Only cells with at least one empty neighbour become rendered cubes
- Interior cells remain in `filled_set` for path-blocking purposes

### Path-Clear Check (grid.py → `is_path_clear`)

- Walks from `grid_key + direction_step` outward
- Fails if any `filled_set` cell is encountered before exiting the bounding volume

### Back-Buffer Color Picking (renderer.py)

- Each cube gets a unique `pick_id` encoded as RGB
- On hover (every frame) and click: re-render flat colors, `glReadPixels` under cursor

### Grading Checklist

- [x] `ortho_matrix()` loaded via `glLoadMatrixf` — no `glOrtho` call
- [x] Global rotation via `compose(rotation_x, rotation_y)` → `glLoadMatrixf`
- [x] Per-cube model matrix from `transform.translation_matrix` → composed MV
- [x] Back-buffer color picking — hover + click
- [x] Path-clear check (outer shell + interior fill)
- [x] Fly-away translation animation via `anim_offset += direction * speed * dt`
- [x] Hover highlight (real-time, every frame)
- [x] Blocked flash (red outline + face tint)
- [x] Large puzzle: 98 / 152 / 218 outer cubes for 5/6/7 sizes
- [x] No external assets

### GROUP-MEMBER
1.Asanti Oluma ugr/8165/16
2.Anatoli chala ugr/4369/16
3.Ebise Tekle ugr/9482/16
4.Mufarihat Tadese ugr/9735/16
5.Marta Tegegn ugr/4457/16
6.Selamawit Mulat ugr/1033/16
7.Solomon waganeh UGR/0092/18


