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

1. Clone this repository:
   ```bash
   git clone https://github.com/fleoxzyy/Arixon-Vision.git
   cd Arixon-Vision
   ```

2. Install the required dependencies:
   ```bash
   pip install opencv-python mediapipe numpy PyQt6 PyQt6-WebEngine
   ```

## 🚀 Usage

Run the main application script:

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
