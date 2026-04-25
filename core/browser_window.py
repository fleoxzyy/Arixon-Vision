"""Browser Window — Floating app launcher overlay with drag support."""

import cv2
import numpy as np


# ── App definitions ──
# Each app: (name, bg_color_bgr, icon_symbol, symbol_color_bgr, launch_action)
# launch_action: "url:..." for web links, "sys:..." for Windows system URIs
APPS = [
    ("YouTube",   (30, 30, 200),   "play",    (255, 255, 255), "internal:YouTube"),
    ("Chrome",    (50, 180, 50),   "chrome",  (255, 255, 255), "internal:Chrome"),
    ("Maps",      (80, 160, 30),   "pin",     (255, 255, 255), "url:https://maps.google.com"),
    ("Photos",    (180, 80, 160),  "img",     (255, 255, 255), "sys:ms-photos:"),
    ("Music",     (180, 60, 120),  "note",    (255, 255, 255), "url:https://music.youtube.com"),
    ("Settings",  (100, 100, 100), "gear",    (220, 220, 220), "sys:ms-settings:"),
    ("Camera",    (200, 140, 40),  "cam",     (255, 255, 255), "sys:microsoft.windows.camera:"),
    ("Files",     (40, 140, 220),  "folder",  (255, 255, 255), "sys:explorer"),
]


def _draw_rounded_rect(img, x, y, w, h, color, radius=8):
    """Draw a filled rounded rectangle."""
    # Main body
    cv2.rectangle(img, (x + radius, y), (x + w - radius, y + h), color, cv2.FILLED)
    cv2.rectangle(img, (x, y + radius), (x + w, y + h - radius), color, cv2.FILLED)
    # Corners
    cv2.circle(img, (x + radius, y + radius), radius, color, cv2.FILLED, cv2.LINE_AA)
    cv2.circle(img, (x + w - radius, y + radius), radius, color, cv2.FILLED, cv2.LINE_AA)
    cv2.circle(img, (x + radius, y + h - radius), radius, color, cv2.FILLED, cv2.LINE_AA)
    cv2.circle(img, (x + w - radius, y + h - radius), radius, color, cv2.FILLED, cv2.LINE_AA)


def _draw_icon_symbol(img, cx, cy, symbol, color, size=16):
    """Draw a simple icon symbol at center (cx, cy)."""
    if symbol == "play":
        # Play triangle
        pts = np.array([
            [cx - size // 3, cy - size // 2],
            [cx - size // 3, cy + size // 2],
            [cx + size // 2, cy],
        ], np.int32)
        cv2.fillPoly(img, [pts], color, cv2.LINE_AA)
    elif symbol == "chrome":
        # Simple globe / circle
        cv2.circle(img, (cx, cy), size // 2, color, 2, cv2.LINE_AA)
        cv2.line(img, (cx - size // 2, cy), (cx + size // 2, cy), color, 1, cv2.LINE_AA)
        cv2.ellipse(img, (cx, cy), (size // 4, size // 2), 0, 0, 360, color, 1, cv2.LINE_AA)
    elif symbol == "pin":
        # Map pin
        cv2.circle(img, (cx, cy - 3), size // 3, color, 2, cv2.LINE_AA)
        pts = np.array([
            [cx - size // 4, cy],
            [cx + size // 4, cy],
            [cx, cy + size // 2],
        ], np.int32)
        cv2.fillPoly(img, [pts], color, cv2.LINE_AA)
    elif symbol == "img":
        # Photo: mountain + sun
        cv2.circle(img, (cx + 4, cy - 4), 3, color, cv2.FILLED, cv2.LINE_AA)
        pts = np.array([
            [cx - size // 2, cy + size // 3],
            [cx - 2, cy - size // 4],
            [cx + 3, cy + 1],
            [cx + size // 2, cy - size // 3],
            [cx + size // 2, cy + size // 3],
        ], np.int32)
        cv2.polylines(img, [pts], False, color, 1, cv2.LINE_AA)
    elif symbol == "note":
        # Music note
        cv2.circle(img, (cx - 2, cy + 4), 4, color, cv2.FILLED, cv2.LINE_AA)
        cv2.line(img, (cx + 2, cy + 4), (cx + 2, cy - size // 2), color, 2, cv2.LINE_AA)
        cv2.line(img, (cx + 2, cy - size // 2), (cx + 6, cy - size // 2 - 2), color, 2, cv2.LINE_AA)
    elif symbol == "gear":
        # Gear: circle with ticks
        cv2.circle(img, (cx, cy), size // 3, color, 2, cv2.LINE_AA)
        for angle in range(0, 360, 45):
            rad = np.radians(angle)
            x1 = int(cx + (size // 3 + 1) * np.cos(rad))
            y1 = int(cy + (size // 3 + 1) * np.sin(rad))
            x2 = int(cx + (size // 2) * np.cos(rad))
            y2 = int(cy + (size // 2) * np.sin(rad))
            cv2.line(img, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)
    elif symbol == "cam":
        # Camera body
        bx, by = cx - size // 3, cy - size // 4
        bw, bh = (size * 2) // 3, size // 2
        cv2.rectangle(img, (bx, by), (bx + bw, by + bh), color, 2, cv2.LINE_AA)
        cv2.circle(img, (cx, cy + 1), size // 5, color, 2, cv2.LINE_AA)
        # Flash bump
        cv2.rectangle(img, (cx - 3, by - 3), (cx + 3, by), color, cv2.FILLED)
    elif symbol == "folder":
        # Folder shape
        fx, fy = cx - size // 3, cy - size // 4
        fw, fh = (size * 2) // 3, size // 2
        cv2.rectangle(img, (fx, fy), (fx + fw, fy + fh), color, 2, cv2.LINE_AA)
        cv2.rectangle(img, (fx, fy - 4), (fx + fw // 3, fy), color, cv2.FILLED)


class BrowserWindow:
    """Floating app-launcher overlay panel with drag support."""

    # Grid layout
    GRID_COLS = 4
    GRID_ROWS = 2
    ICON_SIZE = 48
    ICON_GAP = 14
    LABEL_H = 16

    def __init__(self, width=420, height=310):
        self.w = width
        self.h = height
        self.x = 0
        self.y = 0
        self.target_x = 0
        self.target_y = 0
        self.visible = False
        self.opacity = 0.0
        self._dragging = False
        self._drag_offset = (0, 0)
        self._click_flash = 0
        self._title_h = 32
        self._url_h = 26
        self._tab_text = "Arixon Home"
        self._url_text = "arixon://apps"
        self.hovered_app = None  # Name of app cursor is over, or None
        self.active_app = None
        self.back_btn_rect = None

    def center_on_frame(self, fw, fh):
        self.x = (fw - self.w) // 2
        self.y = (fh - self.h) // 2
        self.target_x = self.x
        self.target_y = self.y

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def start_drag(self, hand_pos):
        if not self.visible:
            return
        self._dragging = True
        self._drag_offset = (hand_pos[0] - self.x, hand_pos[1] - self.y)

    def update_drag(self, hand_pos):
        if self._dragging and self.visible:
            self.target_x = hand_pos[0] - self._drag_offset[0]
            self.target_y = hand_pos[1] - self._drag_offset[1]

    def stop_drag(self):
        self._dragging = False

    def trigger_click(self):
        self._click_flash = 8

    def _get_icon_rects(self):
        """Calculate icon bounding boxes in screen coordinates."""
        content_top = self._title_h + self._url_h + 14
        cell_w = (self.w - 2 * self.ICON_GAP) // self.GRID_COLS
        cell_h = self.ICON_SIZE + self.LABEL_H + 8
        rects = []
        for idx in range(min(len(APPS), self.GRID_COLS * self.GRID_ROWS)):
            col = idx % self.GRID_COLS
            row = idx // self.GRID_COLS
            icon_cx = self.x + self.ICON_GAP + col * cell_w + cell_w // 2
            icon_cy = self.y + content_top + row * (cell_h + 6) + self.ICON_SIZE // 2
            half = self.ICON_SIZE // 2
            rects.append((idx, icon_cx - half, icon_cy - half, icon_cx + half, icon_cy + half))
        return rects

    def get_app_at(self, cursor_x, cursor_y):
        """
        Check if cursor is over an app icon or back button.
        Returns (app_name, launch_action) or (None, None).
        Also updates self.hovered_app.
        """
        if not self.visible or self.opacity < 0.1:
            self.hovered_app = None
            return None, None
            
        if self.active_app:
            if self.back_btn_rect:
                bx1, by1, bx2, by2 = self.back_btn_rect
                if bx1 <= cursor_x <= bx2 and by1 <= cursor_y <= by2:
                    self.hovered_app = "Back"
                    return "Back", "internal:Back"
            self.hovered_app = None
            return None, None

        for idx, x1, y1, x2, y2 in self._get_icon_rects():
            if x1 <= cursor_x <= x2 and y1 <= cursor_y <= y2:
                app = APPS[idx]
                self.hovered_app = app[0]
                return app[0], app[4]  # name, launch_action
        self.hovered_app = None
        return None, None

    def update(self, fw, fh):
        """Update animation state."""
        self.x = int(self.x + (self.target_x - self.x) * 0.3)
        self.y = int(self.y + (self.target_y - self.y) * 0.3)
        self.x = max(0, min(self.x, fw - self.w))
        self.y = max(0, min(self.y, fh - self.h))
        target_op = 0.82 if self.visible else 0.0
        self.opacity += (target_op - self.opacity) * 0.2
        if self.opacity < 0.02:
            self.opacity = 0.0
        if self._click_flash > 0:
            self._click_flash -= 1

    def draw(self, frame):
        """Render app launcher onto frame with alpha blending."""
        if self.opacity < 0.02:
            return
        fh, fw = frame.shape[:2]
        x1, y1 = max(0, self.x), max(0, self.y)
        x2, y2 = min(fw, self.x + self.w), min(fh, self.y + self.h)
        if x2 <= x1 or y2 <= y1:
            return

        roi = frame[y1:y2, x1:x2].copy()
        overlay = roi.copy()
        ow, oh = x2 - x1, y2 - y1
        lx, ly = x1 - self.x, y1 - self.y

        # Background (dark)
        overlay[:] = (35, 30, 25)

        # Title bar (gradient purple-blue)
        tb_y1, tb_y2 = max(0, -ly), min(oh, self._title_h - ly)
        if tb_y2 > tb_y1:
            for row in range(tb_y1, tb_y2):
                t = row / max(self._title_h, 1)
                overlay[row, :] = (int(140 + 40 * t), int(50 + 20 * t), int(60 + 30 * t))

        # Window control dots
        dot_y = self._title_h // 2 - ly
        if 0 <= dot_y < oh:
            for i, color in enumerate([(70, 70, 230), (60, 200, 230), (80, 200, 80)]):
                dx = 16 + i * 18 - lx
                if 0 <= dx < ow:
                    cv2.circle(overlay, (dx, dot_y), 5, color, cv2.FILLED)

        # Tab text
        if self.active_app:
            self._tab_text = self.active_app
            self._url_text = f"https://www.{self.active_app.lower()}.com"
        else:
            self._tab_text = "Arixon Home"
            self._url_text = "arixon://apps"

        tab_ty, tab_tx = self._title_h // 2 + 4 - ly, 80 - lx
        if 0 <= tab_ty < oh and 0 <= tab_tx < ow:
            cv2.putText(overlay, self._tab_text, (tab_tx, tab_ty),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)

        # URL bar
        url_y1, url_y2 = max(0, self._title_h - ly), min(oh, self._title_h + self._url_h - ly)
        if url_y2 > url_y1:
            overlay[url_y1:url_y2, :] = (50, 45, 40)
            
            if self.active_app:
                # Draw back button
                bx, by = 5 - lx, self._title_h + 3 - ly
                bw, bh = 45, self._url_h - 6
                if 0 <= bx < ow and 0 <= by < oh:
                    cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (80, 75, 70), cv2.FILLED)
                    cv2.putText(overlay, "< Back", (bx + 2, by + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1, cv2.LINE_AA)
                    self.back_btn_rect = (self.x + 5, self.y + self._title_h + 3, self.x + 5 + bw, self.y + self._title_h + 3 + bh)
                    if self.hovered_app == "Back":
                        cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (200, 200, 200), 1, cv2.LINE_AA)
                url_tx = 55 - lx
            else:
                self.back_btn_rect = None
                url_tx = 12 - lx

            url_ty = self._title_h + self._url_h // 2 + 4 - ly
            if 0 <= url_ty < oh and 0 <= url_tx < ow:
                cv2.putText(overlay, self._url_text, (url_tx, url_ty),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 180, 180), 1, cv2.LINE_AA)

        content_top = self._title_h + self._url_h

        if self.active_app:
            # Draw Internal App Content
            if self.active_app == "YouTube":
                # Header
                hx, hy = 10 - lx, content_top + 10 - ly
                if 0 <= hx < ow and 0 <= hy < oh:
                    cv2.putText(overlay, "YouTube", (hx, hy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 220), 2, cv2.LINE_AA)
                
                # Video Thumbnails
                for i in range(3):
                    vx, vy = 15 - lx, content_top + 45 + i * 65 - ly
                    if 0 <= vy < oh and 0 <= vx < ow:
                        cv2.rectangle(overlay, (vx, vy), (vx + 90, vy + 55), (60, 60, 60), cv2.FILLED)
                        cv2.putText(overlay, f"Trending Video {i+1}", (vx + 100, vy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)
                        cv2.putText(overlay, "Arixon Channel", (vx + 100, vy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1, cv2.LINE_AA)

            elif self.active_app == "Chrome":
                cx, cy = (ow // 2), content_top + 60 - ly
                if 0 <= cy < oh:
                    # Google text
                    text_size = cv2.getTextSize("Google", cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
                    cv2.putText(overlay, "Google", (cx - text_size[0] // 2, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
                    # Search bar
                    cv2.rectangle(overlay, (cx - 120, cy + 20), (cx + 120, cy + 50), (255, 255, 255), cv2.FILLED)
                    cv2.rectangle(overlay, (cx - 120, cy + 20), (cx + 120, cy + 50), (200, 200, 200), 1, cv2.LINE_AA)
                    cv2.putText(overlay, "Search...", (cx - 110, cy + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1, cv2.LINE_AA)

        else:
            # ── App Grid ──
            cell_w = (self.w - 2 * self.ICON_GAP) // self.GRID_COLS
            cell_h = self.ICON_SIZE + self.LABEL_H + 8

            for idx, (name, bg_color, symbol, sym_color, launch_action) in enumerate(APPS):
                col = idx % self.GRID_COLS
                row = idx // self.GRID_COLS
                if row >= self.GRID_ROWS:
                    break

                # Icon center position (in window-local coords)
                icon_x = self.ICON_GAP + col * cell_w + cell_w // 2
                icon_y = content_top + 14 + row * (cell_h + 6) + self.ICON_SIZE // 2

                # Convert to overlay-local coords
                ox = icon_x - lx
                oy = icon_y - ly

                # Draw rounded icon background
                ix1 = ox - self.ICON_SIZE // 2
                iy1 = oy - self.ICON_SIZE // 2
                if (0 <= ix1 < ow and 0 <= iy1 < oh):
                    _draw_rounded_rect(overlay, ix1, iy1,
                                       self.ICON_SIZE, self.ICON_SIZE,
                                       bg_color, radius=10)
                    # Draw icon symbol
                    _draw_icon_symbol(overlay, ox, oy, symbol, sym_color, size=22)
                    # Hover highlight: bright border around icon
                    if self.hovered_app == name:
                        cv2.rectangle(overlay,
                                      (ix1 - 2, iy1 - 2),
                                      (ix1 + self.ICON_SIZE + 2, iy1 + self.ICON_SIZE + 2),
                                      (255, 255, 255), 2, cv2.LINE_AA)

                # App label below icon
                label_y = oy + self.ICON_SIZE // 2 + 12
                text_size = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.32, 1)[0]
                label_x = ox - text_size[0] // 2
                if 0 <= label_y < oh and 0 <= label_x < ow:
                    cv2.putText(overlay, name, (label_x, label_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1, cv2.LINE_AA)

        # Click flash
        if self._click_flash > 0:
            flash_alpha = self._click_flash / 8.0 * 0.3
            white = np.full_like(overlay, 255)
            cv2.addWeighted(white, flash_alpha, overlay, 1 - flash_alpha, 0, overlay)

        # Border glow
        cv2.rectangle(overlay, (0, 0), (ow - 1, oh - 1), (180, 120, 60), 1, cv2.LINE_AA)

        # Alpha blend
        alpha = min(self.opacity, 0.85)
        cv2.addWeighted(overlay, alpha, roi, 1 - alpha, 0, frame[y1:y2, x1:x2])
