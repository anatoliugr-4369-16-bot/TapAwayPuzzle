"""
main.py  —  Window, game loop, and 2-D HUD.

Screens
-------
  playing  : 3-D block + top HUD + Restart button
  stuck    : "No Moves Available" overlay — Restart / Shuffle / New
  won      : celebration overlay — Restart / New

Controls
--------
  Drag          : rotate view
  Click a cube  : launch (if clear) or red flash (if blocked)
  R             : restart (same puzzle, same arrows)
  5 / 6 / 7     : new puzzle of that size
  S             : shuffle (when stuck)
  ESC           : quit
"""

import sys, math
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *

from renderer   import Renderer
from game_state import GameState

W, H            = 1024, 768
TARGET_FPS      = 60
ROT_SENSITIVITY = 0.36

# ── Palette ──────────────────────────────────────────────────────────
C_PANEL  = ( 16,  22,  38, 215)
C_GOLD   = (238, 198,  46)
C_MINT   = ( 50, 208, 172)
C_CORAL  = (255,  72,  72)
C_WHITE  = (228, 238, 255)
C_MUTED  = ( 88, 108, 148)
C_BTN    = ( 28,  40,  66, 245)
C_BTN_HL = ( 48,  66, 108, 255)


# ── UI helpers ────────────────────────────────────────────────────────

def rrect(surf, color, rect, r=10):
    x, y, w, h = rect
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, color, (0, 0, w, h), border_radius=r)
    surf.blit(s, (x, y))


def star_pts(cx, cy, ro, ri, n=5):
    pts = []
    for i in range(n * 2):
        rr  = ro if i % 2 == 0 else ri
        ang = math.pi / n * i - math.pi / 2
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


class Button:
    def __init__(self, x, y, w, h, label,
                 border=None, text_color=C_WHITE, font=None):
        self.rect       = pygame.Rect(x, y, w, h)
        self.label      = label
        self.border     = border or C_MINT
        self.text_color = text_color
        self.font       = font

    def draw(self, surf, mx, my):
        hov = self.rect.collidepoint(mx, my)
        rrect(surf, C_BTN_HL if hov else C_BTN, self.rect, r=10)
        pygame.draw.rect(surf, self.border, self.rect, width=2, border_radius=10)
        if self.font:
            t = self.font.render(self.label, True, self.text_color)
            surf.blit(t, (self.rect.centerx - t.get_width() // 2,
                          self.rect.centery - t.get_height() // 2))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


# ── HUD draw functions ────────────────────────────────────────────────

def draw_playing_hud(surf, gs, btns, fonts, mx, my, t):
    fsm, fmd, _ = fonts

    # Top bar
    rrect(surf, C_PANEL, (10, 8, W - 20, 62), r=14)

    surf.blit(fsm.render(
        f"TAP AWAY  {gs.puzzle_size}×{gs.puzzle_size}×{gs.puzzle_size}",
        True, C_MUTED), (28, 12))
    surf.blit(fsm.render(f"Taps: {gs.taps}", True, C_MUTED), (28, 36))

    sl = fsm.render("SCORE", True, C_MUTED)
    sv = fmd.render(str(gs.score), True, C_GOLD)
    surf.blit(sl, (W//2 - sl.get_width()//2, 10))
    surf.blit(sv, (W//2 - sv.get_width()//2, 26))

    cr = fsm.render(f"{gs.grid.active_count()} cubes", True, C_MINT)
    surf.blit(cr, (W - 170, 14))

    btns['restart'].draw(surf, mx, my)

    # Bottom hint bar
    rrect(surf, C_PANEL, (10, H - 36, W - 20, 28), r=8)
    hint = fsm.render(
        "Drag → rotate   ·   Click → launch   ·   R restart   ·   5 / 6 / 7 new puzzle   ·   S shuffle",
        True, C_MUTED)
    surf.blit(hint, (W//2 - hint.get_width()//2, H - 30))


def draw_stuck_screen(surf, gs, btns, fonts, mx, my, t):
    fsm, fmd, flg = fonts

    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((4, 8, 18, 195))
    surf.blit(dim, (0, 0))

    cw, ch = 520, 330
    cx = W//2 - cw//2
    cy = H//2 - ch//2
    rrect(surf, (16, 22, 42, 252), (cx, cy, cw, ch), r=22)
    pygame.draw.rect(surf, C_CORAL, (cx+16, cy, cw-32, 5), border_radius=3)

    pulse = 1.0 + 0.04 * math.sin(t * 2.8)
    title = fmd.render("PUZZLE STUCK", True, C_CORAL)
    title = pygame.transform.rotozoom(title, 0, pulse)
    surf.blit(title, (W//2 - title.get_width()//2, cy + 24))

    sub = fsm.render(
        f"{gs.grid.active_count()} cubes remain — no arrow path is clear.",
        True, C_MUTED)
    surf.blit(sub, (W//2 - sub.get_width()//2, cy + 78))

    tip = fsm.render(
        "Shuffle reassigns arrows to break the deadlock  ( −50 pts )",
        True, (65, 85, 115))
    surf.blit(tip, (W//2 - tip.get_width()//2, cy + 106))

    tip2 = fsm.render("Keyboard: R restart · S shuffle", True, (55, 70, 100))
    surf.blit(tip2, (W//2 - tip2.get_width()//2, cy + 132))

    for k in ('stuck_restart', 'stuck_shuffle', 'stuck_new'):
        btns[k].draw(surf, mx, my)


def draw_won_screen(surf, gs, btns, fonts, mx, my, t):
    fsm, fmd, flg = fonts

    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((4, 8, 18, 195))
    surf.blit(dim, (0, 0))

    cw, ch = 490, 345
    cx = W//2 - cw//2
    cy = H//2 - ch//2
    rrect(surf, (14, 20, 36, 252), (cx, cy, cw, ch), r=22)
    pygame.draw.rect(surf, C_MINT, (cx+16, cy, cw-32, 5), border_radius=3)

    pulse = 1.0 + 0.045 * math.sin(t * 3.8)
    title = flg.render("SOLVED!", True, C_MINT)
    title = pygame.transform.rotozoom(title, 0, pulse)
    surf.blit(title, (W//2 - title.get_width()//2, cy + 18))

    n_stars = 3 if gs.taps <= gs.puzzle_size**2 else (2 if gs.taps < 80 else 1)
    bx = W//2 - (3*52)//2
    for i in range(3):
        col = C_GOLD if i < n_stars else (38, 44, 60)
        pygame.draw.polygon(surf, col, star_pts(bx + i*52 + 24, cy + 150, 23, 10))

    sc  = fmd.render(f"{gs.score} pts", True, C_WHITE)
    sub = fsm.render(f"All {gs.taps} cubes cleared!", True, C_MUTED)
    surf.blit(sc,  (W//2 - sc.get_width()//2,  cy + 198))
    surf.blit(sub, (W//2 - sub.get_width()//2, cy + 240))

    for k in ('won_restart', 'won_new'):
        btns[k].draw(surf, mx, my)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    pygame.init()
    pygame.display.set_mode((W, H), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Tap Away")

    fsm = pygame.font.SysFont("monospace", 13, bold=True)
    fmd = pygame.font.SysFont("monospace", 21, bold=True)
    flg = pygame.font.SysFont("monospace", 52, bold=True)
    fonts = (fsm, fmd, flg)

    puzzle_size = 5
    renderer    = Renderer(W, H)
    renderer.setup(puzzle_size)

    gs = GameState()
    gs.start_puzzle(size=puzzle_size)

    clock = pygame.time.Clock()
    t     = 0.0

    # ── Build buttons ────────────────────────────────────────────────
    def make_buttons():
        bx = W // 2
        return {
            # Always-visible (playing HUD)
            'restart':       Button(W-148, 14, 130, 36,
                                    "[ R ] Restart", border=C_MINT, font=fsm),
            # Stuck overlay
            'stuck_restart': Button(bx-248, H//2+80, 148, 44,
                                    "Restart", border=C_MINT, font=fmd),
            'stuck_shuffle': Button(bx- 74, H//2+80, 148, 44,
                                    "Shuffle", border=C_GOLD,
                                    text_color=C_GOLD, font=fmd),
            'stuck_new':     Button(bx+100, H//2+80, 148, 44,
                                    "New Puzzle", border=C_CORAL,
                                    text_color=C_CORAL, font=fmd),
            # Won overlay
            'won_restart':   Button(bx-220, H//2+105, 190, 44,
                                    "Restart", border=C_MINT, font=fmd),
            'won_new':       Button(bx+ 30, H//2+105, 190, 44,
                                    "New Puzzle", border=C_GOLD,
                                    text_color=C_GOLD, font=fmd),
        }

    btns = make_buttons()

    # Mouse state
    dragging   = False
    drag_start = (0, 0)
    last_mouse = (0, 0)
    moved      = False
    hover_pos  = (W//2, H//2)
    mx, my     = hover_pos

    def new_puzzle(size):
        nonlocal puzzle_size, btns
        puzzle_size = size
        renderer.setup(size)
        gs.start_puzzle(size=size)
        renderer.reset_rotation()
        btns = make_buttons()

    # ── Game loop ─────────────────────────────────────────────────────
    while True:
        dt        = clock.tick(TARGET_FPS) / 1000.0
        t        += dt
        click_pos = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif k == pygame.K_r:
                    gs.restart()
                    renderer.reset_rotation()
                elif k == pygame.K_s and gs.is_stuck:
                    gs.shuffle()
                elif k == pygame.K_5: new_puzzle(5)
                elif k == pygame.K_6: new_puzzle(6)
                elif k == pygame.K_7: new_puzzle(7)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging   = True
                drag_start = event.pos
                last_mouse = event.pos
                moved      = False

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                if not moved:
                    click_pos = event.pos

            elif event.type == pygame.MOUSEMOTION:
                hover_pos = event.pos
                mx, my    = hover_pos
                if dragging:
                    dx = event.pos[0] - last_mouse[0]
                    dy = event.pos[1] - last_mouse[1]
                    if (abs(event.pos[0]-drag_start[0]) > 3 or
                            abs(event.pos[1]-drag_start[1]) > 3):
                        moved = True
                    renderer.add_rotation(dy * ROT_SENSITIVITY,
                                          dx * ROT_SENSITIVITY)
                    last_mouse = event.pos

        cubes = gs.grid.cubes

        # ── Button clicks ────────────────────────────────────────────
        if click_pos:
            if gs.is_stuck:
                if btns['stuck_restart'].hit(click_pos):
                    gs.restart(); renderer.reset_rotation()
                elif btns['stuck_shuffle'].hit(click_pos):
                    gs.shuffle()
                elif btns['stuck_new'].hit(click_pos):
                    new_puzzle(puzzle_size)
            elif gs.is_won:
                if btns['won_restart'].hit(click_pos):
                    gs.restart(); renderer.reset_rotation()
                elif btns['won_new'].hit(click_pos):
                    new_puzzle(puzzle_size)
            else:
                if btns['restart'].hit(click_pos):
                    gs.restart(); renderer.reset_rotation()

        # ── Hover picking ────────────────────────────────────────────
        for c in cubes:
            c.hovered = False

        if gs.state == 'playing':
            hx, hy = hover_pos
            renderer.do_pick_pass(cubes, grid=gs.grid)
            pid = renderer.read_pick_color(hx, hy)
            if pid:
                hc = gs.grid.cube_by_pick_id(pid)
                if hc:
                    hc.hovered = True

        # ── Cube click ───────────────────────────────────────────────
        if click_pos and gs.state == 'playing':
            # Don't re-trigger if the click was on a UI button
            if not btns['restart'].hit(click_pos):
                renderer.do_pick_pass(cubes, grid=gs.grid)
                pid = renderer.read_pick_color(*click_pos)
                if pid:
                    cube = gs.grid.cube_by_pick_id(pid)
                    if cube:
                        gs.try_tap(cube)

        # ── Update ──────────────────────────────────────────────────
        gs.update(dt)

        if gs.is_won:
            renderer.add_rotation(0, 20 * dt)   # slow victory spin

        # ── 3-D render ───────────────────────────────────────────────
        renderer.begin_frame()
        renderer.draw_ground_grid(puzzle_size)
        renderer.draw_cubes(cubes, picking_mode=False, grid=gs.grid)

        # ── 2-D HUD overlay ──────────────────────────────────────────
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 0))

        draw_playing_hud(ov, gs, btns, fonts, mx, my, t)

        if gs.is_stuck:
            draw_stuck_screen(ov, gs, btns, fonts, mx, my, t)
        elif gs.is_won:
            draw_won_screen(ov, gs, btns, fonts, mx, my, t)

        raw = pygame.image.tostring(ov, 'RGBA', True)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glWindowPos2i(0, 0)
        glDrawPixels(W, H, GL_RGBA, GL_UNSIGNED_BYTE, raw)

        pygame.display.flip()


if __name__ == '__main__':
    main()
