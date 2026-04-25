"""HUD — Heads-Up Display with FPS counter, status, and gesture info."""

import cv2


# Gesture constants (must match gesture.py)
GESTURE_NONE = "none"
GESTURE_OPEN = "open"
GESTURE_FIST = "fist"
GESTURE_THUMB = "thumb"
GESTURE_PEACE = "peace"
GESTURE_PINCH = "pinch"

GESTURE_LABELS = {
    GESTURE_NONE: "",
    GESTURE_OPEN: "OPEN HAND",
    GESTURE_FIST: "FIST",
    GESTURE_THUMB: "THUMB UP",
    GESTURE_PEACE: "PEACE / DRAG",
    GESTURE_PINCH: "PINCH",
}

GESTURE_ACTIONS = {
    GESTURE_OPEN: ">>  Show Window",
    GESTURE_FIST: ">>  Hide Window",
    GESTURE_THUMB: ">>  Click!",
    GESTURE_PEACE: ">>  Drag Mode",
    GESTURE_PINCH: ">>  Alt Click!",
}


class HUD:
    """On-screen FPS counter, gesture label, and status indicators."""

    @staticmethod
    def _text_shadow(frame, text, pos, scale, color, thickness=1):
        cv2.putText(frame, text, (pos[0] + 1, pos[1] + 1),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
        cv2.putText(frame, text, pos,
                    cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

    def draw(self, frame, fps, gesture, hand_detected):
        fh, fw = frame.shape[:2]

        # FPS counter (top-left)
        self._text_shadow(frame, f"FPS: {int(fps)}", (12, 28), 0.55, (0, 255, 200))

        # Tracking status
        if hand_detected:
            cv2.circle(frame, (14, 50), 6, (0, 220, 0), cv2.FILLED)
            self._text_shadow(frame, "TRACKING", (26, 55), 0.42, (0, 220, 0))
        else:
            cv2.circle(frame, (14, 50), 6, (0, 0, 180), cv2.FILLED)
            self._text_shadow(frame, "NO HAND", (26, 55), 0.42, (0, 0, 180))

        # Gesture label
        label = GESTURE_LABELS.get(gesture, "")
        if label:
            self._text_shadow(frame, label, (12, 82), 0.5, (255, 220, 100))
            action = GESTURE_ACTIONS.get(gesture, "")
            if action:
                self._text_shadow(frame, action, (12, 105), 0.4, (180, 180, 180))

        # Branding (bottom-right)
        self._text_shadow(frame, "Arixon Vision", (fw - 165, fh - 14), 0.45, (140, 140, 140))

        # Controls hint (bottom-left)
        self._text_shadow(frame, "Press Q to quit", (12, fh - 14), 0.35, (100, 100, 100))
