"""Screenshot capture via pyautogui — reference: NIKKEAutoScript."""
import logging

import numpy as np
import pyautogui
import win32gui

logger = logging.getLogger("enikk")


class CaptureMethod:
    """
    Screenshot capture — foreground operation (reference: NIKKEAutoScript).
    Uses pyautogui.screenshot() with window region detection.
    """

    def __init__(self, window_class: str = "UnityWndClass"):
        self.window_class = window_class
        self._hwnd = None

    @property
    def hwnd(self) -> int | None:
        if self._hwnd and win32gui.IsWindow(self._hwnd):
            return self._hwnd
        self._hwnd = self._find_game_window()
        return self._hwnd

    def _find_game_window(self) -> int | None:
        """Find the game window by class name."""
        try:
            hwnd = win32gui.FindWindow(self.window_class, None)
            if hwnd and win32gui.IsWindow(hwnd):
                return hwnd
        except Exception:
            pass
        return None

    @staticmethod
    def _get_window_region(hwnd: int) -> tuple[int, int, int, int]:
        """Get window client region, handling borders and title bar."""
        # Full window rect
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        # Client area (excludes borders/title bar)
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        client_width = client_right - client_left
        client_height = client_bottom - client_top

        # Calculate border offsets
        border_width = (width - client_width) // 2
        border_height = height - client_height - border_width

        return (
            left + border_width,
            top + border_height,
            client_width,
            client_height,
        )

    def capture(self) -> np.ndarray | None:
        """Capture screenshot via pyautogui (foreground operation)."""
        hwnd = self.hwnd
        if not hwnd:
            return None

        try:
            left, top, width, height = self._get_window_region(hwnd)

            # pyautogui uses global screen coordinates
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            image = np.array(screenshot)

            # Convert RGB to BGR for OpenCV
            import cv2
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            return image

        except Exception as e:
            logger.error(f"Capture failed: {e}")
            return None
