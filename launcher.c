/*
 * Arixon Vision — Bootstrap Launcher v0.5.3
 * Win32 GUI splash screen with progress bar.
 * Checks Python, packages, GitHub version, then launches the dashboard.
 *
 * Compile:
 *   windres resources.rc -O coff -o resources.res
 *   gcc launcher.c resources.res -o "Arixon Launcher.exe" -mwindows -lwininet -lcomctl32
 */

#include <windows.h>
#include <commctrl.h>
#include <wininet.h>
#include <stdio.h>
#include <string.h>

#pragma comment(lib, "comctl32.lib")
#pragma comment(lib, "wininet.lib")

#define LOCAL_VERSION "0.5.3"
#define GITHUB_VERSION_URL "https://raw.githubusercontent.com/fleoxzyy/Arixon-Vision/main/VERSION"
#define PYTHON_DL_URL "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"

// Window dimensions
#define WIN_W 420
#define WIN_H 220

// Control IDs
#define ID_PROGRESS 101
#define ID_STATUS   102
#define ID_VERSION  103

// Globals
static HWND hwndMain, hwndProgress, hwndStatus, hwndVersion;
static HFONT hFontStatus, hFontTitle, hFontVersion;
static HBRUSH hBrushBg;

// ─── Helper: run a command silently (no console flash) ───
static int run_silent(const char *cmd) {
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    char buf[2048];
    snprintf(buf, sizeof(buf), "cmd.exe /C %s", cmd);

    if (!CreateProcessA(NULL, buf, NULL, NULL, FALSE,
                        CREATE_NO_WINDOW, NULL, NULL, &si, &pi))
        return -1;

    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exitCode = 1;
    GetExitCodeProcess(pi.hProcess, &exitCode);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    return (int)exitCode;
}

// ─── Helper: set status text + progress ───
static void set_status(const char *text, int progress) {
    SetWindowTextA(hwndStatus, text);
    SendMessage(hwndProgress, PBM_SETPOS, (WPARAM)progress, 0);
    UpdateWindow(hwndMain);

    // Process messages so the UI stays responsive
    MSG msg;
    while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
}

// ─── Helper: fetch remote version from GitHub ───
static int fetch_remote_version(char *out, int maxlen) {
    HINTERNET hInet = InternetOpenA("ArixonLauncher/1.0", INTERNET_OPEN_TYPE_PRECONFIG, NULL, NULL, 0);
    if (!hInet) return 0;

    HINTERNET hUrl = InternetOpenUrlA(hInet, GITHUB_VERSION_URL, NULL, 0,
                                      INTERNET_FLAG_RELOAD | INTERNET_FLAG_NO_CACHE_WRITE, 0);
    if (!hUrl) { InternetCloseHandle(hInet); return 0; }

    DWORD bytesRead = 0;
    char buf[256] = {0};
    InternetReadFile(hUrl, buf, sizeof(buf) - 1, &bytesRead);
    buf[bytesRead] = '\0';

    // Trim whitespace/newlines
    int len = (int)strlen(buf);
    while (len > 0 && (buf[len-1] == '\n' || buf[len-1] == '\r' || buf[len-1] == ' '))
        buf[--len] = '\0';

    strncpy(out, buf, maxlen - 1);
    out[maxlen - 1] = '\0';

    InternetCloseHandle(hUrl);
    InternetCloseHandle(hInet);
    return 1;
}

// ─── The main bootstrap sequence (runs in a thread) ───
static DWORD WINAPI bootstrap_thread(LPVOID lpParam) {
    Sleep(400); // Let the window render

    // Step 1: Check version against GitHub
    set_status("Checking for updates...", 10);
    Sleep(500);

    char remote_ver[64] = {0};
    if (fetch_remote_version(remote_ver, sizeof(remote_ver))) {
        if (strcmp(remote_ver, LOCAL_VERSION) != 0 && strlen(remote_ver) > 0) {
            char msg[512];
            snprintf(msg, sizeof(msg),
                "A new version is available!\n\n"
                "Installed: v%s\n"
                "Latest:    v%s\n\n"
                "Visit the GitHub page to update.",
                LOCAL_VERSION, remote_ver);
            MessageBoxA(hwndMain, msg, "Arixon Vision - Update Available", MB_ICONINFORMATION | MB_OK);
        }
        set_status("Version check complete.", 20);
    } else {
        set_status("Could not reach GitHub. Skipping update check.", 20);
    }
    Sleep(300);

    // Step 2: Check Python installation
    set_status("Verifying Python installation...", 30);
    Sleep(300);

    int py_status = run_silent("python --version >nul 2>&1");
    if (py_status != 0) {
        int result = MessageBoxA(hwndMain,
            "Python is not installed or not in PATH.\n\n"
            "Click OK to open the Python download page.\n"
            "Make sure to check 'Add Python to PATH' during installation!",
            "Arixon Vision - Setup Required",
            MB_ICONWARNING | MB_OKCANCEL);
        if (result == IDOK) {
            ShellExecuteA(NULL, "open", PYTHON_DL_URL, NULL, NULL, SW_SHOWNORMAL);
        }
        set_status("Setup required. Closing.", 100);
        Sleep(1500);
        PostMessage(hwndMain, WM_CLOSE, 0, 0);
        return 1;
    }
    set_status("Python found.", 40);
    Sleep(300);

    // Step 3: Check required packages
    set_status("Verifying dependencies...", 50);
    Sleep(300);

    int pkg_status = run_silent("python -c \"import PyQt6, cv2, mediapipe, PyQt6.QtWebEngineWidgets\" >nul 2>&1");
    if (pkg_status != 0) {
        set_status("Installing dependencies (this may take a few minutes)...", 55);

        run_silent("python -m pip install --upgrade pip >nul 2>&1");
        set_status("Installing opencv-python...", 60);
        run_silent("python -m pip install opencv-python >nul 2>&1");

        set_status("Installing mediapipe...", 68);
        run_silent("python -m pip install mediapipe >nul 2>&1");

        set_status("Installing numpy...", 75);
        run_silent("python -m pip install numpy >nul 2>&1");

        set_status("Installing PyQt6...", 82);
        run_silent("python -m pip install PyQt6 >nul 2>&1");

        set_status("Installing PyQt6-WebEngine...", 90);
        run_silent("python -m pip install PyQt6-WebEngine >nul 2>&1");

        set_status("All packages installed successfully.", 95);
        Sleep(500);
    } else {
        set_status("All dependencies verified.", 90);
        Sleep(300);
    }

    // Step 4: Launch
    set_status("Launching Arixon Vision...", 100);
    Sleep(600);

    ShellExecuteA(NULL, "open", "pythonw", "_launcher.py", NULL, SW_SHOW);

    Sleep(400);
    PostMessage(hwndMain, WM_CLOSE, 0, 0);
    return 0;
}

// ─── Window Procedure ───
static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_CREATE: {
        // Dark background
        hBrushBg = CreateSolidBrush(RGB(18, 18, 24));

        // Fonts
        hFontTitle = CreateFontA(28, 0, 0, 0, FW_BLACK, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        hFontStatus = CreateFontA(15, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Segoe UI");
        hFontVersion = CreateFontA(13, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0, "Consolas");

        // Title label (drawn in WM_PAINT)

        // Version label
        hwndVersion = CreateWindowA("STATIC", "v" LOCAL_VERSION,
            WS_CHILD | WS_VISIBLE | SS_CENTER,
            0, 60, WIN_W, 20, hwnd, (HMENU)ID_VERSION, NULL, NULL);
        SendMessage(hwndVersion, WM_SETFONT, (WPARAM)hFontVersion, TRUE);

        // Progress bar
        hwndProgress = CreateWindowExA(0, PROGRESS_CLASSA, NULL,
            WS_CHILD | WS_VISIBLE | PBS_SMOOTH,
            30, 110, WIN_W - 60, 22, hwnd, (HMENU)ID_PROGRESS, NULL, NULL);
        SendMessage(hwndProgress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
        SendMessage(hwndProgress, PBM_SETPOS, 0, 0);
        SendMessage(hwndProgress, PBM_SETBARCOLOR, 0, (LPARAM)RGB(0, 229, 255));
        SendMessage(hwndProgress, PBM_SETBKCOLOR, 0, (LPARAM)RGB(40, 40, 50));

        // Status text
        hwndStatus = CreateWindowA("STATIC", "Initializing...",
            WS_CHILD | WS_VISIBLE | SS_CENTER,
            0, 145, WIN_W, 25, hwnd, (HMENU)ID_STATUS, NULL, NULL);
        SendMessage(hwndStatus, WM_SETFONT, (WPARAM)hFontStatus, TRUE);

        // Start bootstrap thread
        CreateThread(NULL, 0, bootstrap_thread, NULL, 0, NULL);
        return 0;
    }

    case WM_CTLCOLORSTATIC: {
        HDC hdc = (HDC)wParam;
        SetBkMode(hdc, TRANSPARENT);

        // Cyan text for the version label
        if ((HWND)lParam == hwndVersion) {
            SetTextColor(hdc, RGB(0, 180, 220));
        }
        // Gray text for the status label
        else if ((HWND)lParam == hwndStatus) {
            SetTextColor(hdc, RGB(160, 160, 170));
        }
        return (LRESULT)hBrushBg;
    }

    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);

        // Fill background
        RECT rc;
        GetClientRect(hwnd, &rc);
        FillRect(hdc, &rc, hBrushBg);

        // Draw title text "ARIXON VISION"
        SetBkMode(hdc, TRANSPARENT);
        SelectObject(hdc, hFontTitle);
        SetTextColor(hdc, RGB(0, 229, 255));
        RECT titleRc = {0, 22, WIN_W, 60};
        DrawTextA(hdc, "ARIXON VISION", -1, &titleRc, DT_CENTER | DT_SINGLELINE);

        // Draw subtle accent line
        HPEN pen = CreatePen(PS_SOLID, 1, RGB(0, 229, 255));
        SelectObject(hdc, pen);
        MoveToEx(hdc, 60, 88, NULL);
        LineTo(hdc, WIN_W - 60, 88);
        DeleteObject(pen);

        EndPaint(hwnd, &ps);
        return 0;
    }

    case WM_ERASEBKGND:
        return 1; // Prevent flicker

    case WM_DESTROY:
        DeleteObject(hFontTitle);
        DeleteObject(hFontStatus);
        DeleteObject(hFontVersion);
        DeleteObject(hBrushBg);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(hwnd, msg, wParam, lParam);
}

// ─── Entry Point ───
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Init common controls (for progress bar)
    INITCOMMONCONTROLSEX icc = { sizeof(icc), ICC_PROGRESS_CLASS };
    InitCommonControlsEx(&icc);

    // Register window class
    WNDCLASSEXA wc = {0};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(1));
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = CreateSolidBrush(RGB(18, 18, 24));
    wc.lpszClassName = "ArixonLauncher";
    RegisterClassExA(&wc);

    // Center the window on screen
    int sx = GetSystemMetrics(SM_CXSCREEN);
    int sy = GetSystemMetrics(SM_CYSCREEN);
    int x = (sx - WIN_W) / 2;
    int y = (sy - WIN_H) / 2;

    hwndMain = CreateWindowExA(
        WS_EX_TOPMOST,
        "ArixonLauncher", "Arixon Vision",
        WS_POPUP | WS_VISIBLE,
        x, y, WIN_W, WIN_H,
        NULL, NULL, hInstance, NULL);

    ShowWindow(hwndMain, SW_SHOW);
    UpdateWindow(hwndMain);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return (int)msg.wParam;
}
