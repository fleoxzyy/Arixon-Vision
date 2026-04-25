"""
Hand Tracker — Custom hand tracking using MediaPipe Tasks API.
Replaces cvzone's HandDetector which depends on the removed mp.solutions API.
"""

import cv2
import os
import urllib.request
import mediapipe as mp
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python import BaseOptions


# Path to the hand landmarker model
_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "hand_landmarker.task")


class HandTracker:
    """
    Custom hand tracker using MediaPipe's Tasks API (HandLandmarker).
    Provides landmark detection, finger-up classification, and drawing.
    """

    # Landmark indices
    WRIST = 0
    THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
    RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

    # Skeleton connections for drawing
    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),       # Index
        (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
        (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        (0, 17),                                 # Palm base
    ]

    def __init__(self, min_detection_confidence=0.6, min_tracking_confidence=0.5, num_hands=1):
        if not os.path.exists(_MODEL_PATH):
            print(f"Downloading MediaPipe Hand Landmarker model to {_MODEL_PATH}...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            os.makedirs(os.path.dirname(_MODEL_PATH), exist_ok=True)
            try:
                urllib.request.urlretrieve(url, _MODEL_PATH)
                print("Download complete!")
            except Exception as e:
                raise FileNotFoundError(f"Failed to download model from {url}. Error: {e}")

        options = mp_vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
        self._timestamp_ms = 0

        # Results (pixel coordinates)
        self.landmarks = None       # List of [x, y, z] in pixel coords
        self.hand_center = (0, 0)
        self.index_tip = (0, 0)
        self.thumb_tip = (0, 0)
        self.pinch_dist = 999.0
        self.is_right_hand = True
        self.detected = False

    def detect(self, frame):
        """
        Run hand detection on a BGR frame.
        Returns True if a hand is detected.
        Landmarks are stored in pixel coordinates on this frame's dimensions.
        """
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        self._timestamp_ms += 33  # ~30fps increment
        result = self._landmarker.detect_for_video(mp_image, self._timestamp_ms)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            # Convert normalized landmarks to pixel coordinates
            raw = result.hand_landmarks[0]
            self.landmarks = [
                [lm.x * w, lm.y * h, lm.z * w]  # z scaled by width
                for lm in raw
            ]

            # Handedness
            if result.handedness and len(result.handedness) > 0:
                label = result.handedness[0][0].category_name
                # In a mirrored view, "Left" in MediaPipe = user's right hand
                self.is_right_hand = (label == "Left")

            # Key points
            self.index_tip = (int(self.landmarks[8][0]), int(self.landmarks[8][1]))
            self.thumb_tip = (int(self.landmarks[4][0]), int(self.landmarks[4][1]))

            # Hand center (average of wrist and middle MCP)
            cx = (self.landmarks[0][0] + self.landmarks[9][0]) / 2
            cy = (self.landmarks[0][1] + self.landmarks[9][1]) / 2
            self.hand_center = (int(cx), int(cy))

            # Pinch distance
            dx = self.landmarks[8][0] - self.landmarks[4][0]
            dy = self.landmarks[8][1] - self.landmarks[4][1]
            self.pinch_dist = (dx * dx + dy * dy) ** 0.5

            self.detected = True
        else:
            self.detected = False
            self.landmarks = None

        return self.detected

    def fingers_up(self):
        """
        Determine which fingers are up. Returns [thumb, index, middle, ring, pinky].
        1 = up, 0 = down.
        """
        if self.landmarks is None:
            return [0, 0, 0, 0, 0]

        fingers = []

        # Thumb: compare tip x vs IP joint x (direction depends on handedness)
        if self.is_right_hand:
            fingers.append(1 if self.landmarks[4][0] > self.landmarks[3][0] else 0)
        else:
            fingers.append(1 if self.landmarks[4][0] < self.landmarks[3][0] else 0)

        # Index through Pinky: tip y < PIP y means finger is up (lower y = higher)
        for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            fingers.append(1 if self.landmarks[tip][1] < self.landmarks[pip][1] else 0)

        return fingers

    def draw_hand(self, frame):
        """Draw neon-style hand skeleton on frame."""
        if self.landmarks is None:
            return

        # Glow layer (thick, dim)
        for s, e in self.CONNECTIONS:
            p1 = (int(self.landmarks[s][0]), int(self.landmarks[s][1]))
            p2 = (int(self.landmarks[e][0]), int(self.landmarks[e][1]))
            cv2.line(frame, p1, p2, (80, 60, 0), 6, cv2.LINE_AA)

        # Main lines (neon cyan)
        for s, e in self.CONNECTIONS:
            p1 = (int(self.landmarks[s][0]), int(self.landmarks[s][1]))
            p2 = (int(self.landmarks[e][0]), int(self.landmarks[e][1]))
            cv2.line(frame, p1, p2, (255, 255, 0), 2, cv2.LINE_AA)

        # Joint dots
        for x, y, z in self.landmarks:
            cv2.circle(frame, (int(x), int(y)), 5, (255, 255, 0), cv2.FILLED, cv2.LINE_AA)
            cv2.circle(frame, (int(x), int(y)), 3, (255, 255, 255), cv2.FILLED, cv2.LINE_AA)

    def close(self):
        """Release resources."""
        self._landmarker.close()
