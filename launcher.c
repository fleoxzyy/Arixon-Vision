#include <stdlib.h>
#include <windows.h>
#include <stdio.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // 1. Check if Python is installed and in PATH
    int py_status = system("python --version >nul 2>&1");
    
    if (py_status != 0) {
        int msgboxID = MessageBox(
            NULL,
            "Python is not installed or not added to PATH.\n\nClick OK to open the Python download page.\nMake sure to check 'Add Python to PATH' during installation!",
            "Arixon Vision - Setup Required",
            MB_ICONWARNING | MB_OKCANCEL
        );
        
        if (msgboxID == IDOK) {
            ShellExecute(NULL, "open", "https://www.python.org/downloads/", NULL, NULL, SW_SHOWNORMAL);
        }
        return 1;
    }
    
    // 2. Check if required packages are installed
    int pkg_status = system("python -c \"import PyQt6, cv2, mediapipe, PyQt6.QtWebEngineWidgets\" >nul 2>&1");
    
    if (pkg_status != 0) {
        MessageBox(
            NULL,
            "Required packages are missing.\n\nA command prompt will now open to download and install them automatically. This may take a few minutes.",
            "Arixon Vision - Installing Packages",
            MB_ICONINFORMATION | MB_OK
        );
        
        // Run pip install in a visible console so the user sees progress
        system("python -m pip install --upgrade pip");
        system("python -m pip install opencv-python mediapipe numpy PyQt6 PyQt6-WebEngine");
        
        MessageBox(
            NULL,
            "Installation complete! Arixon Vision will now launch.",
            "Arixon Vision - Success",
            MB_ICONINFORMATION | MB_OK
        );
    }
    
    // 3. Launch the Arixon Vision UI Launcher
    ShellExecute(NULL, "open", "pythonw", "ArixonLauncher.py", NULL, SW_SHOW);
    
    return 0;
}
