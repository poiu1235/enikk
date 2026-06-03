"""Weights management for bundled and user directories."""
import logging
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_bundle_weights_dir() -> Path | None:
    """Get weights directory from bundled package.

    Returns None if no bundled weights found.
    """
    # PyInstaller frozen application
    if getattr(sys, 'frozen', False):
        # In frozen mode, data files are in sys._MEIPASS
        bundle_dir = Path(sys._MEIPASS) / 'weights'
        if bundle_dir.exists():
            return bundle_dir
    # Development mode: weights in package directory
    else:
        dev_dir = Path(__file__).parent.parent / 'weights'
        if dev_dir.exists():
            return dev_dir
    return None


def ensure_weights_ready(user_weights_dir: Path) -> None:
    """Ensure weights are available in user directory.

    If weights not found in user directory, copy from bundled package.

    Args:
        user_weights_dir: Target directory for weights (e.g., %LOCALAPPDATA%/Enikk/weights)
    """
    icon_detect_path = user_weights_dir / 'icon_detect' / 'model.onnx'

    # Weights already exist in user directory
    if icon_detect_path.exists():
        logger.debug(f"Weights already exist at {icon_detect_path}")
        return

    # Get bundled weights
    bundle_weights = get_bundle_weights_dir()
    if not bundle_weights:
        logger.warning("No bundled weights found, weights_dir must be configured manually")
        return

    # Copy weights from bundle to user directory
    try:
        logger.info(f"Copying weights from {bundle_weights} to {user_weights_dir}")
        user_weights_dir.mkdir(parents=True, exist_ok=True)

        # Copy icon_detect directory
        src_icon_detect = bundle_weights / 'icon_detect'
        if src_icon_detect.exists():
            dst_icon_detect = user_weights_dir / 'icon_detect'
            shutil.copytree(src_icon_detect, dst_icon_detect)
            logger.info(f"Weights copied successfully to {dst_icon_detect}")
        else:
            logger.error(f"Bundled weights missing icon_detect directory: {src_icon_detect}")

    except Exception as e:
        logger.error(f"Failed to copy weights: {e}")
