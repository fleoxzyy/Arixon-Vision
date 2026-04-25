"""
Arixon Vision — PyQt6 Edition
A spatial computing simulator optimized for low-end devices.
Uses webcam feed with gesture-controlled real embedded web browser.

Controls:
    Open Hand  — Show browser window
    Fist       — Hide browser window
    Peace Sign — Drag browser window
    Thumb Up   — Click action
    Pinch      — Alt click
"""

import sys
import cv2
import time
import os
import numpy as np

# PyQt6 imports for GUI and embedded browser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsOpacityEffect
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QPoint, QUrl, QPointF
from PyQt6.QtGui import QImage, QPixmap, QMouseEvent

from core.performance import PerformanceManager
from core.gesture import GestureEngine, GESTURE_OPEN, GESTURE_FIST, GESTURE_PEACE, GESTURE_THUMB, GESTURE_PINCH
from core.cursor import ARCursor
from core.hud import HUD


def detect_system_tier():
    """
    Detect system capabilities and return a resolution tier.
    Returns: (width, height, target_fps, detect_every_n, tier_name)
    """
    import ctypes
    
    # Get CPU core count
    cpu_cores = os.cpu_count() or 2
    
    # Get total RAM in GB (Windows-specific, no external packages needed)
    try:
        kernel32 = ctypes.windll.kernel32
        c_ulonglong = ctypes.c_ulonglong
        
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", c_ulonglong),
                ("ullAvailPhys", c_ulonglong),
                ("ullTotalPageFile", c_ulonglong),
                ("ullAvailPageFile", c_ulonglong),
                ("ullTotalVirtual", c_ulonglong),
                ("ullAvailVirtual", c_ulonglong),
                ("ullAvailExtendedVirtual", c_ulonglong),
            ]
        
        mem_info = MEMORYSTATUSEX()
        mem_info.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_info))
        ram_gb = mem_info.ullTotalPhys / (1024 ** 3)
    except Exception:
        ram_gb = 4  # Safe fallback
    
    # Tier selection
    # High:   8+ cores, 8+ GB RAM  → 1280x720, 30fps
    # Medium: 4+ cores, 4+ GB RAM  → 960x720, 25fps
    # Low:    anything else         → 640x480, 20fps
    
    if cpu_cores >= 8 and ram_gb >= 8:
        tier = (1280, 720, 30, 2, "High")
    elif cpu_cores >= 4 and ram_gb >= 4:
        tier = (960, 720, 25, 2, "Medium")
    else:
        tier = (640, 480, 20, 3, "Low")
    
    print(f"  System: {cpu_cores} CPU cores, {ram_gb:.1f} GB RAM")
    print(f"  Performance Tier: {tier[4]} ({tier[0]}x{tier[1]} @ {tier[2]}fps)")
    
    return tier


# Auto-detect best resolution for this PC
SYS_WIDTH, SYS_HEIGHT, SYS_FPS, SYS_DETECT_N, SYS_TIER = detect_system_tier()


class CameraThread(QThread):
    """Runs the OpenCV camera loop and hand tracking in the background to keep the GUI responsive."""
    frame_ready = pyqtSignal(np.ndarray, np.ndarray, dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.gesture_engine = GestureEngine()
        self.perf = PerformanceManager(target_fps=SYS_FPS, detect_every_n=SYS_DETECT_N)
        # Capture at auto-detected resolution
        self.cap_width = SYS_WIDTH
        self.cap_height = SYS_HEIGHT
        
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cap_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cap_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Read actual resolution the camera gave us
        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        while self.running:
            self.perf.frame_start()
            success, frame = cap.read()
            if not success or frame is None:
                continue
                
            frame = cv2.flip(frame, 1)
            
            # Resize to target dimensions if camera gave different resolution
            if frame.shape[1] != self.cap_width or frame.shape[0] != self.cap_height:
                frame = cv2.resize(frame, (self.cap_width, self.cap_height))
            
            fh, fw = frame.shape[:2]
            
            found = False
            if self.perf.should_detect():
                # Downscale for performance (still process at 320x240 for speed)
                small = cv2.resize(frame, (320, 240))
                found = self.gesture_engine.detect(small)
                
                # Scale landmarks back up to full resolution
                if found and self.gesture_engine.landmarks is not None:
                    sx = fw / 320.0
                    sy = fh / 240.0
                    tracker = self.gesture_engine.tracker
                    tracker.landmarks = [[lm[0]*sx, lm[1]*sy, lm[2]*sx] for lm in tracker.landmarks]
                    tracker.index_tip = (int(tracker.index_tip[0]*sx), int(tracker.index_tip[1]*sy))
                    tracker.thumb_tip = (int(tracker.thumb_tip[0]*sx), int(tracker.thumb_tip[1]*sy))
                    tracker.hand_center = (int(tracker.hand_center[0]*sx), int(tracker.hand_center[1]*sy))
                    dx = tracker.landmarks[8][0] - tracker.landmarks[4][0]
                    dy = tracker.landmarks[8][1] - tracker.landmarks[4][1]
                    tracker.pinch_dist = (dx*dx + dy*dy)**0.5
            else:
                found = self.gesture_engine.tracker.detected
            
            # Create a separate BGR canvas for hand drawing
            hand_canvas = np.zeros((fh, fw, 3), dtype=np.uint8)
            self.gesture_engine.draw_hand(hand_canvas)
            
            # Convert hand canvas to a transparent RGBA overlay
            gray = cv2.cvtColor(hand_canvas, cv2.COLOR_BGR2GRAY)
            _, alpha = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
            b, g, r = cv2.split(hand_canvas)
            overlay_frame = cv2.merge((b, g, r, alpha))

            self.perf.update_fps()
            
            state = {
                'gesture': self.gesture_engine.gesture,
                'hand_found': found,
                'hand_center': self.gesture_engine.tracker.hand_center,
                'index_tip': self.gesture_engine.tracker.index_tip,
                'fps': self.perf.fps
            }
            
            self.frame_ready.emit(frame, overlay_frame, state)
            self.perf.wait()
            
        cap.release()
        self.gesture_engine.close()

    def stop(self):
        self.running = False
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arixon Vision - MR Camera Overlay")
        self.resize(SYS_WIDTH, SYS_HEIGHT)
        self.setMinimumSize(640, 480)
        
        # Central widget to hold everything
        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        
        # Background Camera Feed
        self.bg_label = QLabel(self.central)
        self.bg_label.setGeometry(0, 0, SYS_WIDTH, SYS_HEIGHT)
        self.bg_label.setScaledContents(True)
        
        # Floating Browser Container
        self.browser_widget = QWidget(self.central)
        self.browser_widget.setGeometry(
            int(SYS_WIDTH * 0.10), int(SYS_HEIGHT * 0.10),
            int(SYS_WIDTH * 0.75), int(SYS_HEIGHT * 0.75)
        )
        self.browser_widget.setStyleSheet("""
            QWidget#BrowserContainer {
                background-color: rgba(30, 30, 35, 220);
                border-radius: 12px;
                border: 2px solid #555;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        self.browser_widget.setObjectName("BrowserContainer")
        
        layout = QVBoxLayout(self.browser_widget)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Top App Toolbar
        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(30)
        t_layout = QHBoxLayout(self.toolbar)
        t_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_yt = QPushButton("YouTube")
        btn_yt.clicked.connect(lambda: self.web_view.setUrl(QUrl("https://www.youtube.com")))
        btn_chrome = QPushButton("Google")
        btn_chrome.clicked.connect(lambda: self.web_view.setUrl(QUrl("https://www.google.com")))
        btn_maps = QPushButton("Maps")
        btn_maps.clicked.connect(lambda: self.web_view.setUrl(QUrl("https://maps.google.com")))
        
        t_layout.addWidget(btn_yt)
        t_layout.addWidget(btn_chrome)
        t_layout.addWidget(btn_maps)
        t_layout.addStretch()
        
        # The REAL Web Browser Engine
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://www.youtube.com"))
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.web_view)
        
        # Semi-transparent Glass effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0.90)
        self.browser_widget.setGraphicsEffect(self.opacity_effect)
        self.browser_widget.hide()  # hidden by default
        
        # Transparent Overlay Label for Hand/Cursor (ALWAYS ON TOP)
        self.overlay_label = QLabel(self.central)
        self.overlay_label.setGeometry(0, 0, SYS_WIDTH, SYS_HEIGHT)
        self.overlay_label.setScaledContents(True)
        self.overlay_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay_label.setStyleSheet("background: transparent;")
        self.overlay_label.raise_()
        
        # Overlay states
        self.cursor = ARCursor()
        self.hud = HUD()
        
        self.was_dragging = False
        self.was_resizing = False
        self.drag_offset = (0, 0)
        self.resize_start = (0, 0)
        self.resize_start_size = (0, 0)
        self.prev_gesture = "none"
        self.last_click_time = 0
        self.RESIZE_CORNER_SIZE = 60  # px from corner to trigger resize
        
        # Start Camera Loop
        self.thread = CameraThread()
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.start()

    def resizeEvent(self, event):
        """Dynamically resize all layers when the window is resized."""
        super().resizeEvent(event)
        w = self.central.width()
        h = self.central.height()
        
        # Resize background and overlay to fill the window
        self.bg_label.setGeometry(0, 0, w, h)
        self.overlay_label.setGeometry(0, 0, w, h)
        self.overlay_label.raise_()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Q:
            self.close()

    def simulate_click(self, x, y):
        """Simulate a mouse click inside the QWebEngineView using Qt Events."""
        # Scale coordinates from camera space to window space
        w = self.central.width()
        h = self.central.height()
        sx = w / self.thread.cap_width
        sy = h / self.thread.cap_height
        screen_x = int(x * sx)
        screen_y = int(y * sy)
        
        local_pos = self.browser_widget.mapFromParent(QPoint(screen_x, screen_y))
        # Ensure click is actually inside the web view (not just the toolbar)
        if self.web_view.geometry().contains(local_pos):
            web_pos = self.web_view.mapFromParent(local_pos)
            target = self.web_view.focusProxy() or self.web_view
            
            p_pos = QPointF(float(web_pos.x()), float(web_pos.y()))
            press = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                p_pos, p_pos,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            release = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                p_pos, p_pos,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier
            )
            
            QApplication.sendEvent(target, press)
            QApplication.sendEvent(target, release)
            print("  >> Simulated Click on Web View")
            
        elif self.toolbar.geometry().contains(local_pos):
            # Click on toolbar buttons
            tool_pos = self.toolbar.mapFromParent(local_pos)
            child = self.toolbar.childAt(tool_pos)
            if child:
                p_pos = QPointF(float(tool_pos.x()), float(tool_pos.y()))
                press = QMouseEvent(
                    QMouseEvent.Type.MouseButtonPress, p_pos, p_pos,
                    Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
                )
                release = QMouseEvent(
                    QMouseEvent.Type.MouseButtonRelease, p_pos, p_pos,
                    Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier
                )
                QApplication.sendEvent(child, press)
                QApplication.sendEvent(child, release)
                print(f"  >> Simulated Click on App Toolbar")

    def update_frame(self, frame, overlay_frame, state):
        g = state['gesture']
        found = state['hand_found']
        cx, cy = state['hand_center']
        ix, iy = state['index_tip']
        fps = state['fps']
        
        # Get current window dimensions for coordinate scaling
        win_w = self.central.width()
        win_h = self.central.height()
        cam_w = self.thread.cap_width
        cam_h = self.thread.cap_height
        sx = win_w / cam_w
        sy = win_h / cam_h
        
        # Scale hand coordinates from camera space to window space
        scx, scy = int(cx * sx), int(cy * sy)
        six, siy = int(ix * sx), int(iy * sy)
        
        # 1. Handle browser visibility
        if g == GESTURE_OPEN:
            if not self.browser_widget.isVisible():
                self.browser_widget.show()
                self.overlay_label.raise_() # ensure overlay stays on top
        elif g == GESTURE_FIST:
            if self.browser_widget.isVisible():
                self.browser_widget.hide()
                
        # 2. Handle dragging OR resizing
        if g == GESTURE_PEACE and found and self.browser_widget.isVisible():
            bw = self.browser_widget
            br = bw.geometry()
            
            # Check if hand is near bottom-right corner (resize zone)
            corner_x = br.x() + br.width()
            corner_y = br.y() + br.height()
            near_corner = (abs(scx - corner_x) < self.RESIZE_CORNER_SIZE and 
                          abs(scy - corner_y) < self.RESIZE_CORNER_SIZE)
            
            if not self.was_dragging and not self.was_resizing:
                # Decide: resize or drag?
                if near_corner:
                    self.was_resizing = True
                    self.resize_start = (scx, scy)
                    self.resize_start_size = (br.width(), br.height())
                else:
                    self.was_dragging = True
                    self.drag_offset = (scx - br.x(), scy - br.y())
            
            if self.was_resizing:
                # Resize mode
                dx = scx - self.resize_start[0]
                dy = scy - self.resize_start[1]
                new_w = max(200, self.resize_start_size[0] + dx)
                new_h = max(150, self.resize_start_size[1] + dy)
                new_w = min(new_w, win_w - br.x())
                new_h = min(new_h, win_h - br.y())
                
                # Smooth resize
                curr_w = bw.width()
                curr_h = bw.height()
                bw.resize(int(curr_w + (new_w - curr_w)*0.3), int(curr_h + (new_h - curr_h)*0.3))
                
            elif self.was_dragging:
                # Drag mode
                new_x = scx - self.drag_offset[0]
                new_y = scy - self.drag_offset[1]
                new_x = max(0, min(new_x, win_w - bw.width()))
                new_y = max(0, min(new_y, win_h - bw.height()))
                curr_x = bw.x()
                curr_y = bw.y()
                bw.move(int(curr_x + (new_x - curr_x)*0.3), int(curr_y + (new_y - curr_y)*0.3))
        else:
            self.was_dragging = False
            self.was_resizing = False

        # 3. Handle clicking
        now = time.time()
        if g in (GESTURE_THUMB, GESTURE_PINCH) and self.prev_gesture != g:
            if now - self.last_click_time > 0.5: # 0.5s cooldown
                self.simulate_click(ix, iy)
                self.last_click_time = now
        self.prev_gesture = g
        
        # 4. Update Cursor State
        cursor_state = ARCursor.STATE_IDLE
        if found and self.browser_widget.isVisible():
            if self.browser_widget.geometry().contains(six, siy):
                cursor_state = ARCursor.STATE_HOVER
        if g in (GESTURE_THUMB, GESTURE_PINCH):
            cursor_state = ARCursor.STATE_CLICK
            
        self.cursor.update((ix, iy), cursor_state, found)
        
        # Draw cursor onto the overlay frame (in camera space)
        fh, fw = frame.shape[:2]
        temp_cursor_bgr = np.zeros((fh, fw, 3), dtype=np.uint8)
        self.cursor.draw(temp_cursor_bgr)
        gray_cursor = cv2.cvtColor(temp_cursor_bgr, cv2.COLOR_BGR2GRAY)
        _, alpha_cursor = cv2.threshold(gray_cursor, 1, 255, cv2.THRESH_BINARY)
        b, g_ch, r = cv2.split(temp_cursor_bgr)
        cursor_rgba = cv2.merge((b, g_ch, r, alpha_cursor))
        
        # Combine the hand overlay and cursor overlay
        mask = alpha_cursor > 0
        overlay_frame[mask] = cursor_rgba[mask]
        
        # 5. Update HUD (HUD is drawn on the background frame)
        self.hud.draw(frame, fps, g, found)
        
        # 6. Convert OpenCV frame to QPixmap and set background
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        self.bg_label.setPixmap(QPixmap.fromImage(qimg))
        
        # 7. Convert Overlay frame to QPixmap and set overlay label
        qimg_overlay = QImage(overlay_frame.data, w, h, w * 4, QImage.Format.Format_RGBA8888)
        self.overlay_label.setPixmap(QPixmap.fromImage(qimg_overlay))


def main():
    print("=" * 50)
    print("  Arixon Vision — PyQt6 Real WebEngine Edition")
    print("  Starting up...")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()