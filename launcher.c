#include <stdlib.h>
#include <windows.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Hide the console window
    FreeConsole();
    
    // Execute the Python launcher
    // Using system() works but it might flash a terminal. 
    // ShellExecute is better to avoid the flash.
    ShellExecute(NULL, "open", "pythonw", "ArixonLauncher.py", NULL, SW_SHOW);
    
    return 0;
}
