import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QWidget, QLabel
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QTextCursor

class ArixonLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arixon Vision Launcher")
        self.setFixedSize(700, 500)
        
        # Fancy Dark Theme CSS
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel#Title { 
                color: #00e5ff; font-size: 32px; font-weight: 900; 
                font-family: 'Segoe UI', Arial; letter-spacing: 2px;
                margin-top: 10px;
            }
            QLabel#Sub { 
                color: #888; font-size: 14px; font-family: 'Segoe UI', Arial; 
                margin-bottom: 20px; font-weight: 500;
            }
            QPushButton { 
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00e5ff, stop:1 #0088cc);
                color: #000; font-weight: 800; font-size: 16px; 
                border-radius: 8px; padding: 12px; letter-spacing: 1px;
            }
            QPushButton:hover { 
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #33eeff, stop:1 #00aaff);
            }
            QPushButton:disabled { 
                background-color: #333; color: #666; border: 1px solid #444;
            }
            QTextEdit { 
                background-color: #0a0a0a; color: #00ff00; font-family: 'Consolas', 'Courier New';
                font-size: 13px; border: 1px solid #333; border-radius: 8px; padding: 10px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(30, 20, 30, 30)
        
        # Header
        title = QLabel("ARIXON VISION")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sub = QLabel("SPATIAL COMPUTING ENGINE")
        sub.setObjectName("Sub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Launch Button
        self.btn_launch = QPushButton("LAUNCH ENGINE")
        self.btn_launch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_launch.clicked.connect(self.start_app)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.append("<span style='color: #00e5ff;'>[SYSTEM] Arixon Launcher Initialized.</span>")
        self.log_area.append("<span style='color: #888;'>Waiting for user command...</span><br>")
        
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addWidget(self.btn_launch)
        layout.addSpacing(15)
        layout.addWidget(self.log_area)
        
        # Subprocess Management
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state)
        
    def start_app(self):
        self.btn_launch.setEnabled(False)
        self.btn_launch.setText("ENGINE RUNNING...")
        self.log_area.append("<br><span style='color: #00ff00;'>[SYSTEM] Booting Arixon Vision core...</span>")
        # Start python script
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
                    # Treat warnings from MediaPipe as normal logs but yellow
                    self.log_area.append(f"<span style='color: #aaaa00;'>[LOG] {line}</span>")
                else:
                    self.log_area.append(f"<span style='color: #ff5555;'>[ERROR] {line}</span>")
        self.log_area.moveCursor(QTextCursor.MoveOperation.End)

    def handle_state(self, state):
        if state == QProcess.ProcessState.NotRunning:
            self.btn_launch.setEnabled(True)
            self.btn_launch.setText("LAUNCH ENGINE")
            self.log_area.append("<br><span style='color: #ffaa00;'>[SYSTEM] Application Terminated.</span>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArixonLauncher()
    window.show()
    sys.exit(app.exec())
