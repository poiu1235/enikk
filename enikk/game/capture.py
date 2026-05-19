"""Screenshot capture by window handle."""
from __future__ import annotations

import logging

import cv2
import numpy as np
import pyautogui

from . import window

logger = logging.getLogger("enikk")


class CaptureService:
    """Stateless screenshot capture for a window client area."""

    def __init__(self, window_service: window.WindowService | None = None, *_, **__):
        self.window = window_service or window.WindowService()

    def capture(self, hwnd: int, *, activate: bool = True) -> np.ndarray | None:
        """Capture a window client area as a BGR image."""
        if not self.window.is_valid(hwnd):
            logger.error("Capture failed: invalid hwnd=%r", hwnd)
            return None

        try:
            if activate:
                self.window.force_foreground(hwnd)

            region = self.window.get_client_region(hwnd)
            if region is None:
                logger.error("Capture failed: hwnd=%d has no client region", hwnd)
                return None

            screenshot = pyautogui.screenshot(region=region.as_tuple())
            image = np.array(screenshot)

            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error("Capture failed for hwnd=%d: %s", hwnd, e, exc_info=True)
            return None


CaptureMethod = CaptureService
