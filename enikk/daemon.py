"""Enikk daemon — game state capture, analysis, and actions."""
import base64
import logging
import threading
import time

import cv2
import numpy as np

from . import capture, process
from .config import Config
from . import analyzer
from . import input as input_mod
from .ui_parser import UIParser

logger = logging.getLogger("enikk")

COMPRESS_SIZE = (1366, 768)


class Daemon:
    def __init__(self, config: Config):
        self.config = config
        self.proc_mgr = process.ProcessManager(
            launcher_path=config.launcher_path,
            game_path=config.game_path,
            launcher_process=config.launcher_process_name,
            game_process=config.game_process_name,
            window_class=config.window_class,
            timeout=config.launch_timeout,
        )
        self.capture = capture.CaptureMethod(config.window_class, config.game_path)
        self.input = input_mod.Input(hwnd=self.capture.hwnd)
        self.ui_parser = UIParser(getattr(config, 'weights_dir', None))
        self._latest_state: analyzer.GameState | None = None
        self._lock = threading.Lock()
        self.stop_event = threading.Event()

    def stop(self):
        """Signal the daemon to stop."""
        logger.info("Stop requested, shutting down...")
        self.stop_event.set()

    def init(self, auto_launch: bool = False):
        """Initialize the daemon."""
        if auto_launch:
            self.launch_and_wait()

    def launch_and_wait(self) -> bool:
        """Full launch flow: Launcher → Login → Game."""
        return self.proc_mgr.app_start(stop_event=self.stop_event)

    def analyze(self, frame: np.ndarray | None = None) -> analyzer.GameState:
        """Capture screenshot, compress, run UI parser, return structured state."""
        compressed = cv2.resize(frame, COMPRESS_SIZE)
        _, buf = cv2.imencode(".jpeg", compressed)
        image_b64 = base64.b64encode(buf.tobytes()).decode()

        parsed = self.ui_parser.parse(frame)

        bbox_desc = "All element bbox coordinates are normalized to [0, 1000] as [x1, y1, x2, y2], where (x1,y1) is top-left and (x2,y2) is bottom-right, as percentages of screen width and height."

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

    # ── Actions ──

    def action_click(self, x: int, y: int) -> dict:
        """Click at normalized [0, 1000] coordinates."""
        off_x, off_y, w, h = 0, 0, COMPRESS_SIZE[0], COMPRESS_SIZE[1]
        region = self.capture.get_region()
        if region:
            off_x, off_y, w, h = region
        self.input.set_hwnd(self.capture.hwnd)
        abs_x = off_x + int(x / 1000 * w)
        abs_y = off_y + int(y / 1000 * h)
        self.input.mouse_click(abs_x, abs_y)
        return {"success": True, "x": abs_x, "y": abs_y}

    def action_exit(self) -> dict:
        """Force-terminate the game process."""
        result = self.proc_mgr.game.stop()
        self._latest_state = None
        self.input.set_hwnd(None)
        return {"success": result, "message": "Game terminated" if result else "Failed"}
