"""Screenshot capture via pyautogui."""
import ctypes
import logging

import cv2
import numpy as np
import pyautogui
import psutil
import win32gui
import win32process

logger = logging.getLogger("enikk")


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

    import time
    time.sleep(0.05)
    return win32gui.GetForegroundWindow() == hwnd


class CaptureMethod:
    """
    Screenshot capture — foreground operation.
    Uses pyautogui.screenshot() with window region detection.
    """

    def __init__(self, window_class: str = "UnityWndClass", process_path: str = ""):
        self.window_class = window_class
        self.process_path = process_path
        self._hwnd = None

    @property
    def hwnd(self) -> int | None:
        if self._hwnd and win32gui.IsWindow(self._hwnd):
            return self._hwnd
        self._hwnd = self._find_window()
        return self._hwnd

    def _find_window(self) -> int | None:
        """Find window by class name + process path."""
        hwnd_list = []

        def enum_windows_callback(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                class_name = win32gui.GetClassName(hwnd)
                if class_name != self.window_class:
                    return

                # If process_path is set, match by executable path
                if self.process_path:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        proc = psutil.Process(pid)
                        if proc.exe().lower() != self.process_path.lower():
                            return
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        return

                hwnd_list.append(hwnd)
            except Exception:
                pass

        win32gui.EnumWindows(enum_windows_callback, hwnd_list)

        if hwnd_list:
            hwnd = hwnd_list[0]
            title = win32gui.GetWindowText(hwnd)
            logger.info(f"Found window class '{self.window_class}', hwnd={hwnd}, title='{title}'")
            return hwnd

        logger.debug(f"No window found for class '{self.window_class}', path='{self.process_path}'")
        return None

    @staticmethod
    def _get_window_region(hwnd: int) -> tuple[int, int, int, int] | None:
        """Get window client region, handling borders and title bar."""
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        border_width = (width - client_width) // 2
        border_height = height - client_height - border_width

        if client_width <= 0 or client_height <= 0:
            logger.debug(f"Window has no client area: {client_width}x{client_height}")
            return None

        return (
            left + border_width,
            top + border_height,
            client_width,
            client_height,
        )

    def get_region(self) -> tuple[int, int, int, int] | None:
        """Get the window region in screen coordinates (left, top, width, height)."""
        hwnd = self.hwnd
        if not hwnd:
            return None
        return self._get_window_region(hwnd)

    def activate(self) -> bool:
        """Bring game window to foreground."""
        self._activate_window()
        return self.hwnd is not None

    def _activate_window(self):
        """Force game window to foreground."""
        hwnd = self.hwnd
        if not hwnd:
            return
        try:
            foreground = win32gui.GetForegroundWindow()
            if foreground != hwnd:
                logger.debug("Activating game window hwnd=%d", hwnd)
                force_foreground(hwnd)
        except Exception as e:
            logger.warning("Failed to activate window: %s", e)

    def capture(self, activate: bool = True) -> np.ndarray | None:
        """Capture screenshot of game window region.

        Args:
            activate: If True, bring game window to foreground before capture.
        """
        hwnd = self.hwnd
        if hwnd is None:
            logger.error(
                "Game window not found — class='%s', path='%s'. "
                "Is the game running?",
                self.window_class, self.process_path,
            )
            return None
        try:
            if activate:
                self._activate_window()
            region = self._get_window_region(hwnd)
            if region is None:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                logger.error(
                    "Window found but has no client area — hwnd=%d, rect=%dx%d",
                    hwnd, right - left, bottom - top,
                )
                return None
            left, top, width, height = region

            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            image = np.array(screenshot)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image
        except Exception as e:
            logger.error("Capture failed for hwnd=%d: %s", hwnd, e, exc_info=True)
            return None
