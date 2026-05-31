"""Pytest configuration — mock heavy native dependencies for unit tests."""
import sys
from unittest.mock import MagicMock

# Mock native modules that aren't available in test environments.
# These are imported transitively via controller.py and game modules.
_heavy_modules = [
    "cv2", "win32gui", "numpy", "pyautogui", "pynput", "mss",
    "enikk.game", "enikk.game.capture", "enikk.game.input",
    "enikk.game.process", "enikk.game.window", "enikk.ui_parser",
]
for mod_name in _heavy_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()
