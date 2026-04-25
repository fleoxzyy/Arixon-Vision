# Arixon Vision 🕶️

A lightweight, spatial computing camera overlay built with Python. Designed to run on low-end hardware, Arixon Vision turns your webcam feed into an interactive Mixed-Reality interface, allowing you to browse the web entirely using hand gestures.

## ✨ Features

- **Real Embedded Browser:** Browse YouTube, Google, and Maps inside the AR overlay using `PyQt6-WebEngine`.
- **Gesture Control:** Interact with the digital world using simple hand gestures:
  - ✋ **Open Hand**: Show / hide the browser overlay.
  - ✌️ **Peace Sign**: Grab and drag the window around your screen.
  - 👍 **Thumb Up** or 🤏 **Pinch**: Click on links, videos, and buttons.
- **Glassmorphism UI:** Beautiful, semi-transparent rendering using PyQt and OpenCV.
- **Highly Optimized:** Utilizes frame-skipping, downscaling, and multi-threading (`QThread`) to maintain stable FPS even on budget CPUs. Uses the modern MediaPipe Tasks API for blazing-fast hand tracking.

## 🛠️ Installation

**Zero-Setup Method (Recommended):**
1. Clone this repository or download the ZIP.
2. Double-click **`Arixon Launcher.exe`**.
3. *That's it!* The launcher will automatically detect if you have Python installed (and prompt you to download it if not). It will then automatically download all required pip packages and AI models in the background before launching the dashboard.

**Manual Method (For Developers):**
1. Clone this repository:
   ```bash
   git clone https://github.com/fleoxzyy/Arixon-Vision.git
   cd Arixon-Vision
   ```
2. Install the required dependencies:
   ```bash
   pip install opencv-python mediapipe numpy PyQt6 PyQt6-WebEngine
   ```
*(Note: The AI Hand Landmarker model will automatically download itself the first time you run the script!)*

## 🚀 Usage

You can launch the application in two ways:

1. **Using the UI Launcher (Recommended):**
   Simply double-click the **`Arixon Launcher.exe`** file. This will open a beautiful dark-themed dashboard where you can click "LAUNCH ENGINE" and view system logs and errors in real-time.

2. **Using the Command Line:**
   ```bash
   python ArixonVision.py
   ```

### Controls:
- **Press `Q`** on your keyboard to safely exit the application.

## 🧠 Architecture
- **`ArixonVision.py`**: The main entry point containing the PyQt6 GUI and multi-threading loop.
- **`core/gesture.py`**: Handles hand landmark detection, state tracking, and drawing the AR neon skeleton.
- **`core/cursor.py`**: Manages the glowing cursor that follows your index finger.
- **`core/performance.py`**: Manages FPS tracking and dynamic frame-skipping logic.
- **`core/hud.py`**: Renders the Heads-Up Display (FPS counter and active gesture).

## License
MIT License
