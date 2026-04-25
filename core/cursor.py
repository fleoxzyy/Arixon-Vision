"""AR Cursor — Glowing cursor controlled by index fingertip."""

import cv2
import numpy as np


class ARCursor:
    """Glowing cursor that follows the index fingertip."""

    STATE_IDLE = 0
    STATE_HOVER = 1
    STATE_CLICK = 2

    def __init__(self):
        self.x = 0
        self.y = 0
        self.sx = 0.0  # smoothed
        self.sy = 0.0
        self.state = self.STATE_IDLE
        self.visible = False
        self._pulse = 0.0

    def update(self, pos, state, visible):
        self.visible = visible
        if visible:
            self.sx += (pos[0] - self.sx) * 0.45
            self.sy += (pos[1] - self.sy) * 0.45
            self.x = int(self.sx)
            self.y = int(self.sy)
        self.state = state
        self._pulse += 0.15

    def draw(self, frame):
        if not self.visible:
            return
        colors = {
            self.STATE_IDLE: (0, 220, 0),
            self.STATE_HOVER: (220, 180, 0),
            self.STATE_CLICK: (0, 0, 240),
        }
        color = colors.get(self.state, (0, 220, 0))
        pulse_r = int(14 + 3 * abs(np.sin(self._pulse)))
        # Outer glow ring
        cv2.circle(frame, (self.x, self.y), pulse_r, color, 1, cv2.LINE_AA)
        # Inner dot
        cv2.circle(frame, (self.x, self.y), 5, color, cv2.FILLED, cv2.LINE_AA)
        cv2.circle(frame, (self.x, self.y), 3, (255, 255, 255), cv2.FILLED, cv2.LINE_AA)
