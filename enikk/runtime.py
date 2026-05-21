"""Enikk game runtime orchestration."""
from __future__ import annotations

import base64
import logging
import threading
import time

import cv2
import numpy as np

from . import analyzer
from .config import Config, GameConfig
from .game import capture, input as input_mod, process, window
from .runtimes.nikke import nikke_profile_from_config
from .runtimes.profile import GameProfile
from .ui_parser import MAX_DIM, UIParser

logger = logging.getLogger(__name__)
DEFAULT_MAX_DIM = 1366


def profile_from_config(config: Config) -> GameProfile:
    return nikke_profile_from_config(config)


class GameRuntime:
    """Stateful orchestrator for one game runtime."""

    def __init__(self, config: Config):
        self.config = config
        self.profile = profile_from_config(config)

        gc = config.games.get("nikke", GameConfig())
        self.process_manager = process.GameProcessManager(
            self.profile,
            timeout=gc.launch_timeout,
        )
        self.window_service = window.WindowService()
        self.capture_service = capture.CaptureService(self.window_service)
        self.input_service = input_mod.InputService(self.window_service)

        self.max_dim = MAX_DIM
        self.ui_parser = UIParser(config.workspace.weights_dir)

        self.game_hwnd: int | None = None
        self.launcher_hwnd: int | None = None
        self._latest_state: analyzer.GameState | None = None
        self._lock = threading.Lock()
        self.stop_event = threading.Event()

    def stop(self):
        logger.info("Stop requested, shutting down...")
        self.stop_event.set()

    def init(self, auto_launch: bool = False):
        if auto_launch:
            self.launch_and_wait()

    def get_game_hwnd(self) -> int | None:
        if self.window_service.is_valid(self.game_hwnd):
            return self.game_hwnd

        self.game_hwnd = self.window_service.find_by_path_and_class(
            self.profile.game_path,
            self.profile.game_window_class,
        )
        return self.game_hwnd

    def get_launcher_hwnd(self) -> int | None:
        if not self.profile.launcher_path:
            return None
        if self.window_service.is_valid(self.launcher_hwnd):
            return self.launcher_hwnd

        self.launcher_hwnd = self.window_service.find_by_path_and_class(
            self.profile.launcher_path,
            self.profile.launcher_window_class,
        )
        return self.launcher_hwnd

    def launch_and_wait(self) -> bool:
        pm = self.process_manager
        pm._last_error = ""

        if pm.game.is_running():
            hwnd = self.get_game_hwnd()
            if hwnd:
                self.window_service.force_foreground(hwnd)
                return True
            pm._last_error = "Game running but window not found"
            logger.warning("Game running but window not found, restarting...")
            pm.stop_game()

        starter = pm.launcher or pm.game
        if not starter.is_running() and not starter.start():
            pm._last_error = f"{starter.name} failed to start"
            return False

        if starter is pm.launcher:
            launcher_hwnd = self._wait_until_value(self.get_launcher_hwnd, timeout=30)
            if launcher_hwnd:
                self.window_service.force_foreground(launcher_hwnd)

        gc = self.config.games.get("nikke", GameConfig())
        if not self._wait_until(pm.game.is_running, timeout=gc.launch_timeout):
            pm._last_error = "Timeout waiting for game process"
            logger.error(pm._last_error)
            return False

        game_hwnd = self._wait_until_value(self.get_game_hwnd, timeout=60)
        if not game_hwnd:
            pm._last_error = "Timeout waiting for game window"
            logger.error(pm._last_error)
            return False

        self.window_service.force_foreground(game_hwnd)
        logger.info("Game started successfully")
        return True

    def _wait_until(self, condition, timeout: int, period: float = 1.0) -> bool:
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.stop_event.is_set():
                self.process_manager._last_error = "Cancelled"
                return False
            if condition():
                return True
            time.sleep(period)
        return False

    def _wait_until_value(self, getter, timeout: int, period: float = 1.0):
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.stop_event.is_set():
                self.process_manager._last_error = "Cancelled"
                return None
            value = getter()
            if value:
                return value
            time.sleep(period)
        return None

    def analyze(self, frame: np.ndarray | None = None) -> analyzer.GameState:
        """Capture screenshot, compress, run UI parser, return structured state."""
        if frame is None:
            hwnd = self.get_game_hwnd()
            if not hwnd:
                raise ValueError("Game window not found")
            frame = self.capture_service.capture(hwnd)
        if frame is None:
            raise ValueError("Failed to capture screenshot")

        h, w = frame.shape[:2]
        max_dim = getattr(self, "max_dim", DEFAULT_MAX_DIM)
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            compressed = cv2.resize(frame, (int(w * scale), int(h * scale)))
        else:
            compressed = frame

        _, buf = cv2.imencode(".jpeg", compressed)
        image_b64 = base64.b64encode(buf.tobytes()).decode()
        parsed = self.ui_parser.parse(frame)
        bbox_desc = (
            "All element bbox coordinates are normalized to [0, 1000] as "
            "[x1, y1, x2, y2], where (x1,y1) is top-left and (x2,y2) is "
            "bottom-right, as percentages of screen width and height."
        )

        state = analyzer.GameState(
            image_b64=image_b64,
            width=compressed.shape[1],
            height=compressed.shape[0],
            ocr=parsed,
            bbox_desc=bbox_desc,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        )
        with self._lock:
            self._latest_state = state
        return state

    def action_click(self, x: int, y: int) -> dict:
        """Click at normalized [0, 1000] coordinates."""
        hwnd = self.get_game_hwnd()
        if not hwnd:
            return {"success": False, "error": "Game window not available"}
        return self.input_service.click_normalized(hwnd, x, y)

    def action_exit(self) -> dict:
        result = self.process_manager.stop_game()
        self._latest_state = None
        self.game_hwnd = None
        return {"success": result, "message": "Game terminated" if result else "Failed"}

    def shutdown(self):
        self.stop_event.set()
        logger.info("Runtime shut down")