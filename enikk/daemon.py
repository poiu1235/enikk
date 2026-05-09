"""Enikk daemon — game state capture, analysis, and actions."""
import logging
import threading
import time

from . import capture, process
from .config import Config
from . import analyzer, input as input_mod

logger = logging.getLogger("enikk")


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
        self.analyzer = analyzer.GameAnalyzer(config.assets_dir) if hasattr(config, 'assets_dir') else analyzer.GameAnalyzer()
        self.input = input_mod.Input()
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

    def analyze(self) -> analyzer.GameState:
        """Capture + analyze current game state."""
        frame = self.capture.capture()
        if frame is None:
            state = analyzer.GameState(
                game_state="not_running",
                state_reason="capture_failed",
                actions=["launch_game"],
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )
            self._latest_state = state
            return state

        state = self.analyzer.analyze(frame)
        with self._lock:
            self._latest_state = state
        return state

    # ── Actions ──

    def action_click(self, x: int, y: int) -> dict:
        """Click at screen coordinates."""
        self.input.mouse_click(x, y)
        return {"success": True, "x": x, "y": y}

    def action_exit(self) -> dict:
        """Force-terminate the game process."""
        result = self.proc_mgr.game.stop()
        self._latest_state = None
        return {"success": result, "message": "Game terminated" if result else "Failed"}
