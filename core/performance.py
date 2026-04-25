"""Performance manager — FPS limiting, frame skipping, timing."""

import time


class PerformanceManager:
    """Controls FPS limiting, frame skipping, and timing."""

    def __init__(self, target_fps=25, detect_every_n=2):
        self.target_fps = target_fps
        self.min_frame_time = 1.0 / target_fps
        self.detect_every_n = detect_every_n
        self.frame_count = 0
        self.fps = 0.0
        self._fps_samples = []
        self._last_time = time.perf_counter()
        self._frame_start = time.perf_counter()

    def frame_start(self):
        self._frame_start = time.perf_counter()
        self.frame_count += 1

    def should_detect(self):
        return self.frame_count % self.detect_every_n == 0

    def update_fps(self):
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now
        if dt > 0:
            self._fps_samples.append(1.0 / dt)
        if len(self._fps_samples) > 15:
            self._fps_samples.pop(0)
        self.fps = sum(self._fps_samples) / max(len(self._fps_samples), 1)

    def wait(self):
        elapsed = time.perf_counter() - self._frame_start
        sleep_time = self.min_frame_time - elapsed
        if sleep_time > 0.001:
            time.sleep(sleep_time)
