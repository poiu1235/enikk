"""Enikk CLI — single entrypoint for daemon, screenshot, and click commands."""
import argparse
import io
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, quote
from urllib.request import urlopen, urlretrieve

from .config import Config
from .daemon import Daemon
from .server import create_app
import uvicorn


# ── HTTP helpers ──────────────────────────────────────────────────────

def build_url(base: str) -> str:
    if not base.startswith("http"):
        base = f"http://{base}"
    return base


logger = logging.getLogger("enikk")


# ── Daemon command ────────────────────────────────────────────────────

def cmd_daemon(args):
    """Start the Enikk daemon process."""
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.config:
        cfg = Config.from_yaml(args.config)
    else:
        cfg = Config.from_env()

    if args.launcher_path:
        cfg.launcher_path = args.launcher_path
    if args.game_path:
        cfg.game_path = args.game_path
    if args.port:
        cfg.port = args.port

    daemon = Daemon(cfg)

    if sys.platform == 'win32':
        def handler(sig, frame):
            daemon.stop()
            os._exit(0)
        signal.signal(signal.SIGINT, handler)

    daemon.init()

    logger.info(f"Starting API server on {cfg.host}:{cfg.port}")
    try:
        uvicorn.run(create_app(daemon), host=cfg.host, port=cfg.port, log_level="info")
    except KeyboardInterrupt:
        pass
    finally:
        daemon.stop()


# ── Client commands ───────────────────────────────────────────────────

def cmd_screenshot(args):
    fmt = args.format or "jpeg"
    ext = "jpg" if fmt == "jpeg" else "png"
    save_dir_param = getattr(args, "save_dir", "") or ""
    width_param = getattr(args, "width", "") or ""
    if args.output:
        out = args.output
    else:
        save_dir = Path("screenshots")
        save_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = str(save_dir / f"{ts}.{ext}")
    qs = f"format={fmt}&debug={args.debug}&save_dir={quote(save_dir_param)}"
    if width_param:
        qs += f"&width={width_param}"
    urlretrieve(urljoin(build_url(args.server), f"/api/screenshot?{qs}"), out)
    print(f"Screenshot saved to {out}")


def cmd_click(args):
    url = urljoin(build_url(args.server), f"/api/action/click?x={args.x}&y={args.y}")
    resp = urlopen(url, timeout=10)
    data = json.loads(resp.read())
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if data.get("success"):
        print(f"Clicked at ({data.get('x')},{data.get('y')})")


# ── Main entrypoint ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="enikk", description="Enikk — The CLI for NIKKE: Goddess of Victory"
    )
    parser.add_argument("--server", default="127.0.0.1:18931", help="Daemon server address")
    sub = parser.add_subparsers(dest="command")

    # Daemon subcommand
    daemon_p = sub.add_parser("daemon", help="Start the game monitor daemon")
    daemon_p.add_argument("--config", type=str, help="Path to YAML config file")
    daemon_p.add_argument("--launcher-path", type=str, help="Path to NIKKE launcher")
    daemon_p.add_argument("--game-path", type=str, help="Path to NIKKE game exe")
    daemon_p.add_argument("--port", type=int, help="API port")
    daemon_p.set_defaults(func=cmd_daemon)

    screenshot_p = sub.add_parser("screenshot", help="Download latest screenshot")
    screenshot_p.add_argument("-f", "--format", choices=["jpeg", "png"], default="jpeg")
    screenshot_p.add_argument("-o", "--output", help="Output file path")
    screenshot_p.add_argument("-d", "--save-dir", help="Directory to save screenshot")
    screenshot_p.add_argument("--debug", action="store_true", help="Add debug overlay")
    screenshot_p.add_argument("-w", "--width", type=int, help="Resize width")
    screenshot_p.set_defaults(func=cmd_screenshot)

    click_p = sub.add_parser("click", help="Click at screen coordinates")
    click_p.add_argument("x", type=int, help="Screen X")
    click_p.add_argument("y", type=int, help="Screen Y")
    click_p.set_defaults(func=cmd_click)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except URLError as e:
        print(f"Error: cannot connect to {getattr(args, 'server', 'unknown')} — {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
