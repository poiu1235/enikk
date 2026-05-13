"""Windows window management utilities."""
import ctypes
import time

import win32gui
import win32process

SW_SHOWNORMAL = 1

_user32 = ctypes.WinDLL("user32")
_kernel32 = ctypes.WinDLL("kernel32")

_kernel32.GetCurrentThreadId.argtypes = []
_kernel32.GetCurrentThreadId.restype = ctypes.c_ulong

_user32.AttachThreadInput.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_bool]
_user32.AttachThreadInput.restype = ctypes.c_bool

_user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
_user32.SetForegroundWindow.restype = ctypes.c_bool

_user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
_user32.ShowWindow.restype = ctypes.c_bool

_user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
_user32.SetWindowPos.restype = ctypes.c_bool


def force_foreground(hwnd: int) -> bool:
    """Force a window to the foreground, bypassing Windows foreground lock."""
    try:
        _user32.ShowWindow(hwnd, SW_SHOWNORMAL)
    except Exception:
        pass

    fg_hwnd = win32gui.GetForegroundWindow()
    if fg_hwnd == hwnd:
        return True

    fg_tid = win32process.GetWindowThreadProcessId(fg_hwnd)[0]
    my_tid = _kernel32.GetCurrentThreadId()

    if fg_tid != my_tid:
        _user32.AttachThreadInput(fg_tid, my_tid, True)

    try:
        _user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
        _user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002)
        _user32.SetForegroundWindow(hwnd)
    finally:
        if fg_tid != my_tid:
            _user32.AttachThreadInput(fg_tid, my_tid, False)

    time.sleep(0.05)
    return win32gui.GetForegroundWindow() == hwnd
