"""Gesture Engine — Gesture classification with stabilization."""

from core.hand_tracker import HandTracker


# Gesture constants
GESTURE_NONE = "none"
GESTURE_OPEN = "open"       # ✋ Show browser
GESTURE_FIST = "fist"       # ✊ Hide browser
GESTURE_THUMB = "thumb"     # 👍 Click
GESTURE_PEACE = "peace"     # ✌️ Drag
GESTURE_PINCH = "pinch"     # 🤏 Alt-click


class GestureEngine:
    """Hand detection with gesture classification and stabilization."""

    def __init__(self):
        self.tracker = HandTracker(
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
            num_hands=1,
        )
        self.gesture = GESTURE_NONE
        self._gesture_buffer = []
        self._stable_gesture = GESTURE_NONE
        self._stability_frames = 3

    # Expose tracker properties for convenience
    @property
    def landmarks(self):
        return self.tracker.landmarks

    @property
    def hand_center(self):
        return self.tracker.hand_center

    @property
    def index_tip(self):
        return self.tracker.index_tip

    @property
    def thumb_tip(self):
        return self.tracker.thumb_tip

    @property
    def pinch_dist(self):
        return self.tracker.pinch_dist

    def detect(self, frame):
        """Run hand detection and classify gesture. Returns True if hand found."""
        found = self.tracker.detect(frame)
        if found:
            self._classify()
        else:
            self._update_stable(GESTURE_NONE)
        return found

    def _classify(self):
        fingers = self.tracker.fingers_up()
        pinch = self.tracker.pinch_dist

        if pinch < 35:
            raw = GESTURE_PINCH
        elif sum(fingers) >= 4:  # 4-5 fingers up = open hand
            raw = GESTURE_OPEN
        elif sum(fingers) == 0:
            raw = GESTURE_FIST
        elif fingers[0] == 1 and sum(fingers[1:]) == 0:
            raw = GESTURE_THUMB
        elif fingers[1] == 1 and fingers[2] == 1 and sum(fingers) <= 3:
            raw = GESTURE_PEACE
        else:
            raw = GESTURE_NONE
        self._update_stable(raw)

    def _update_stable(self, raw):
        self._gesture_buffer.append(raw)
        if len(self._gesture_buffer) > self._stability_frames:
            self._gesture_buffer.pop(0)
        if all(g == raw for g in self._gesture_buffer):
            self._stable_gesture = raw
        self.gesture = self._stable_gesture

    def draw_hand(self, frame):
        """Draw hand skeleton on frame."""
        self.tracker.draw_hand(frame)

    def close(self):
        """Release resources."""
        self.tracker.close()
