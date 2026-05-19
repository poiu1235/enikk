"""NIKKE game profile."""
from __future__ import annotations

from .model import GameProfile

NAME = "nikke"
DEFAULT_GAME_PATH = r"C:\Program Files\NIKKE\NIKKE.exe"
DEFAULT_LAUNCHER_PATH = r"C:\Program Files\NIKKE\launcher\nikke_launcher.exe"
GAME_WINDOW_CLASS = "UnityWndClass"
LAUNCHER_WINDOW_CLASS = "TWINCONTROL"


def create(
    *,
    exe_path: str = DEFAULT_GAME_PATH,
    launcher_path: str | None = DEFAULT_LAUNCHER_PATH,
    game_window_class: str = GAME_WINDOW_CLASS,
    launcher_window_class: str | None = LAUNCHER_WINDOW_CLASS,
) -> GameProfile:
    """Create a NIKKE profile."""
    return GameProfile(
        name=NAME,
        exe_path=exe_path,
        launcher_path=launcher_path,
        game_window_class=game_window_class,
        launcher_window_class=launcher_window_class,
    )


def from_config(config) -> GameProfile:
    """Create a NIKKE profile from the application config."""
    return create(
        exe_path=getattr(config, "game_path", DEFAULT_GAME_PATH),
        launcher_path=getattr(config, "launcher_path", DEFAULT_LAUNCHER_PATH),
        game_window_class=getattr(config, "window_class", GAME_WINDOW_CLASS),
        launcher_window_class=getattr(config, "launcher_window_class", LAUNCHER_WINDOW_CLASS),
    )
