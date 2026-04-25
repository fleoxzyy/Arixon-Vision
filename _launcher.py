import sys
import math
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QWidget, QLabel, QFrame
from PyQt6.QtCore import QProcess, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QTextCursor, QPainter, QLinearGradient, QColor, QPen, QFont


class AnimatedBackground(QWidget):
    """Animated particle/grid background for the launcher."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)  # 20fps for background animation
        
        # Generate grid points
        self._dots = []
        for x in range(0, 800, 40):
            for y in range(0, 600, 40):
                self._dots.append((x, y))

    def _animate(self):
        self._tick += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # Dark gradient background
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(8, 8, 18))
        grad.setColorAt(0.5, QColor(12, 15, 30))
        grad.setColorAt(1.0, QColor(5, 5, 15))
        painter.fillRect(0, 0, w, h, grad)
        
        # Animated grid dots
        t = self._tick * 0.03
        for dx, dy in self._dots:
            # Scale dots to widget size
            px = dx * w / 800
            py = dy * h / 600
            
            # Subtle wave animation
            offset = math.sin(t + dx * 0.01 + dy * 0.008) * 0.5 + 0.5
            alpha = int(20 + offset * 35)
            size = 1.5 + offset * 1.0
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 229, 255, alpha))
            painter.drawEllipse(int(px - size/2), int(py - size/2), int(size), int(size))
        
        # Glowing horizontal line accent
        line_y = int(h * 0.38)
        glow_grad = QLinearGradient(0, 0, w, 0)
        glow_grad.setColorAt(0.0, QColor(0, 229, 255, 0))
        glow_grad.setColorAt(0.3, QColor(0, 229, 255, 60))
        glow_grad.setColorAt(0.5, QColor(0, 229, 255, 100))
        glow_grad.setColorAt(0.7, QColor(0, 229, 255, 60))
        glow_grad.setColorAt(1.0, QColor(0, 229, 255, 0))
        painter.setPen(QPen(glow_grad, 1))
        painter.drawLine(0, line_y, w, line_y)
        
        painter.end()


class ArixonLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arixon Vision")
        self.setFixedSize(750, 520)
        
        # Main container
        self.central = QWidget(self)
        self.setCentralWidget(self.central)
        
        # Animated background
        self.bg = AnimatedBackground(self.central)
        self.bg.setGeometry(0, 0, 750, 520)
        
        # Content overlay
        content = QWidget(self.central)
        content.setGeometry(0, 0, 750, 520)
        content.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # ─── Header ───
        title = QLabel("ARIXON VISION")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 34, QFont.Weight.Black))
        title.setStyleSheet("color: #00e5ff; letter-spacing: 6px; background: transparent;")
        
        sub = QLabel("PUBLIC BETA")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        sub.setStyleSheet("color: rgba(255,255,255,0.4); letter-spacing: 4px; background: transparent; margin-bottom: 5px;")

        version = QLabel("v0.5.3")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setFont(QFont("Consolas", 10))
        version.setStyleSheet("color: rgba(0,229,255,0.5); background: transparent; margin-bottom: 15px;")
        
        # ─── Divider ───
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: rgba(0,229,255,0.15); background: transparent;")
        
        # ─── Launch Button ───
        self.btn_launch = QPushButton("▶  LAUNCH ENGINE")
        self.btn_launch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_launch.setFixedHeight(50)
        self.btn_launch.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.btn_launch.clicked.connect(self.start_app)
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0,229,255,200), stop:1 rgba(0,136,204,200));
                color: #000;
                border: none;
                border-radius: 10px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(51,238,255,230), stop:1 rgba(0,170,255,230));
            }
            QPushButton:disabled {
                background: rgba(50,50,60,180);
                color: rgba(255,255,255,0.3);
                border: 1px solid rgba(0,229,255,0.15);
            }
        """)
        
        # ─── Status Indicator ───
        self.status_label = QLabel("●  IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setFont(QFont("Consolas", 10))
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.35); background: transparent; margin-top: 10px;")
        
        # ─── Log Area ───
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 11))
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(5,5,12,200);
                color: #00ff00;
                border: 1px solid rgba(0,229,255,0.12);
                border-radius: 10px;
                padding: 12px;
                selection-background-color: rgba(0,229,255,0.3);
            }
        """)
        self.log_area.append("<span style='color: #00e5ff;'>[SYSTEM] Arixon Launcher v0.5.3 Initialized.</span>")
        self.log_area.append("<span style='color: rgba(255,255,255,0.3);'>Ready. Click LAUNCH ENGINE to start.</span><br>")
        
        # ─── Layout Assembly ───
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addWidget(version)
        layout.addWidget(divider)
        layout.addSpacing(8)
        layout.addWidget(self.btn_launch)
        layout.addWidget(self.status_label)
        layout.addSpacing(5)
        layout.addWidget(self.log_area)
        
        # ─── Subprocess Management ───
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state)
        
    def start_app(self):
        self.btn_launch.setEnabled(False)
        self.btn_launch.setText("■  ENGINE RUNNING")
        self.status_label.setText("●  RUNNING")
        self.status_label.setStyleSheet("color: #00ff88; background: transparent; margin-top: 10px;")
        self.log_area.append("<br><span style='color: #00ff00;'>[SYSTEM] Launching Arixon Vision core...</span>")
        self.process.start("python", ["_engine.py"])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        for line in data.splitlines():
            if line.strip():
                self.log_area.append(f"<span style='color: #cccccc;'>{line}</span>")
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        for line in data.splitlines():
            if line.strip():
                if "W0000" in line or "Created TensorFlow Lite" in line:
                    self.log_area.append(f"<span style='color: #aaaa00;'>[LOG] {line}</span>")
                else:
                    self.log_area.append(f"<span style='color: #ff5555;'>[ERROR] {line}</span>")
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def handle_state(self, state):
        if state == QProcess.ProcessState.NotRunning:
            self.btn_launch.setEnabled(True)
            self.btn_launch.setText("▶  LAUNCH ENGINE")
            self.status_label.setText("●  STOPPED")
            self.status_label.setStyleSheet("color: #ff5555; background: transparent; margin-top: 10px;")
            self.log_area.append("<br><span style='color: #ffaa00;'>[SYSTEM] Engine stopped.</span>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArixonLauncher()
    window.show()
    sys.exit(app.exec())
