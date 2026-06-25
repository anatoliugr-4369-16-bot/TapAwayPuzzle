"""
input_handler.py
Member responsibility: Mouse input only (drag rotation + click selection).
Keyboard is handled directly in main.py via pygame.key.get_pressed().
"""

import pygame

ROTATION_SENSITIVITY = 0.4


class InputHandler:
    def __init__(self):
        self._dragging   = False
        self._last_mouse = (0, 0)
        self._drag_start = (0, 0)
        self._moved      = False

        self.rotation_delta_x    = 0.0
        self.rotation_delta_y    = 0.0
        self.clicked_screen_pos  = None
        self.quit_requested      = False

    def process_events(self):
        self.rotation_delta_x   = 0.0
        self.rotation_delta_y   = 0.0
        self.clicked_screen_pos = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_requested = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._dragging   = True
                self._drag_start = event.pos
                self._last_mouse = event.pos
                self._moved      = False

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging = False
                if not self._moved:
                    self.clicked_screen_pos = event.pos

            elif event.type == pygame.MOUSEMOTION and self._dragging:
                dx = event.pos[0] - self._last_mouse[0]
                dy = event.pos[1] - self._last_mouse[1]
                tdx = event.pos[0] - self._drag_start[0]
                tdy = event.pos[1] - self._drag_start[1]
                if abs(tdx) > 3 or abs(tdy) > 3:
                    self._moved = True
                self.rotation_delta_y += dx * ROTATION_SENSITIVITY
                self.rotation_delta_x += dy * ROTATION_SENSITIVITY
                self._last_mouse = event.pos
