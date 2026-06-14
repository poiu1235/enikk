"""Bootstrap script for PyInstaller — imports enikk package and runs main."""
import sys
import traceback


def _show_error(msg: str) -> None:
    """Display error to user. MessageBox in release mode, console in debug."""
    detail = traceback.format_exc()
    full = f"{msg}\n\n{detail}"

    # Try Windows MessageBox (works in release mode without console)
    try:
        import ctypes
        MB_OK = 0x0
        MB_ICONERROR = 0x10
        ctypes.windll.user32.MessageBoxW(
            0, full, "Enikk — Startup Error", MB_OK | MB_ICONERROR,
        )
    except Exception:
        pass

    # Also write to a log file next to the exe
    try:
        import os
        exe_dir = os.path.dirname(sys.executable)
        log_path = os.path.join(exe_dir, "enikk_error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(full)
    except Exception:
        pass

    # Console fallback (debug mode)
    print(full, file=sys.stderr)
    try:
        input("Press Enter to exit...")
    except Exception:
        pass


try:
    from enikk.__main__ import main
    main()
except Exception as e:
    _show_error(f"Failed to start Enikk: {e}")
    sys.exit(1)
