# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Enikk — NIKKE: Goddess of Victory CLI

Automation tool for the NIKKE game. Designed as a daemon that exposes an HTTP API; external AI agents consume the JSON state and orchestrate decisions.

## Architecture

```
CLI (cli.py) ──HTTP──▶ FastAPI Server (server.py) ──▶ Daemon (daemon.py)
                                                      ├── ProcessManager (process.py)
                                                      ├── CaptureMethod (capture.py)
                                                      ├── GameAnalyzer (analyzer.py)
                                                      ├── UIParser (ui_parser.py)
                                                      ├── Input (input.py)
                                                      └── force_foreground (window_utils.py)

CLI ──agent──▶ AgentRunner (agent/runner.py) ──hermes-agent──▶ Tools (agent/hermes_tools.py)
                                                             ──▶ Prompts (agent/prompts.py)
```

| Module | Responsibility |
|--------|---------------|
| `cli.py` | Single entrypoint with `argparse` subcommands (daemon, screenshot, click, agent) |
| `server.py` | FastAPI HTTP server with Timing middleware. Launch endpoint runs in a background thread via `threading.Thread(daemon=True)` to avoid blocking the event loop |
| `daemon.py` | Central `Daemon` class wiring process, capture, analyzer, ui_parser, and input |
| `process.py` | Full launch flow: Launcher → Login → Game via `app_start()`. Split into `_Process` base, `LauncherProcess` (adds OCR login), `GameProcess` |
| `capture.py` | pyautogui screenshots of game window region via EnumWindows + psutil path matching |
| `analyzer.py` | RapidOCR + CV-based state detection (loading, lobby, popup, launcher, login) |
| `ui_parser.py` | OmniParser-style UI analysis: YOLO icon detection + RapidOCR text recognition, outputs normalized [0,1000] bboxes |
| `input.py` | Foreground input via pyautogui/pynput; background input via win32 PostMessage |
| `window_utils.py` | `force_foreground()` — bypasses Windows foreground lock via AttachThreadInput |
| `config.py` | Dataclass config with YAML + env override support + agent defaults |
| `agent/runner.py` | `AgentRunner` — wraps hermes-agent AIAgent with screenshot/click/wait tools, trajectory saving, and post-session review |
| `agent/hermes_tools.py` | Hermes tool registry bindings: `_screenshot`, `_click`, `_wait` via daemon HTTP API |
| `agent/prompts.py` | System prompts for AGENT_SYSTEM_PROMPT and REVIEW_SYSTEM_PROMPT |

## Development Commands

```powershell
# Virtual environment
uv venv --seed
.venv\Scripts\Activate.ps1

# Install (editable)
uv pip install -e .

# Run daemon
enikk daemon

# Run daemon with custom paths
enikk daemon --launcher-path "D:\NIKKE\launcher.exe" --game-path "D:\NIKKE\game.exe"

# Run daemon with config file
enikk daemon --config config.yaml

# Client commands (requires daemon running)
enikk screenshot -o screen.jpg
enikk click 960 540

# AI agent (requires daemon running + LLM API configured)
enikk agent "navigate to the daily missions" --config config.yaml
enikk agent "complete the current event" --model qwen3.6-plus --base-url https://api.example.com --api-key sk-xxx
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/state` | Current game state (on-demand capture + analyze) |
| GET | `/api/state/stream` | SSE state stream |
| GET | `/api/screenshot` | Screenshot base64 + OCR + YOLO UI elements |
| GET | `/api/process` | Game process info |
| POST | `/api/action/launch` | Launch game (async, returns immediately) |
| GET | `/api/action/click` | Click at (x, y) — normalized [0,1000] |
| POST | `/api/action/exit` | Terminate game |
| GET | `/api/info` | API metadata + endpoint list |

## Key Design Decisions

- **CLI does atomic operations; agents orchestrate flows.** The CLI exposes deterministic endpoints (state, screenshot, click, etc.) without complex branching logic.
- **Launch is async.** `/api/action/launch` starts the launch in a background thread via `threading.Thread(daemon=True)` and returns immediately. The client should poll `/api/state` or `/api/process` for progress. A `threading.Event` is used for cooperative cancellation, triggered by Ctrl-C signal handler.
- **Foreground-only input.** The game uses Unity/Windows input that requires the window to be in the foreground. pyautogui captures global screenshots and simulates input.
- **UIParser: YOLO + OCR fusion.** Screenshots are compressed to max 1366px dimension, then processed by both RapidOCR and YOLO in parallel. Overlap resolution prefers OCR text inside YOLO icon boxes, discarding redundant detections. All bboxes are normalized to [0,1000] for agent-agnostic coordinate mapping.
- **RapidOCR for text detection.** Uses `rapidocr-onnxruntime` (CPU, ~16MB model) instead of cloud-based OCR.
- **Hermes AI agent.** The `enikk agent` command runs a hermes-agent AIAgent with screenshot/click/wait tools. After each session, a review agent extracts lessons to persistent memory for future sessions. Trajectories are saved as JSONL.
- **Build backend** uses standard `setuptools.build_meta`. Package discovery is constrained to `enikk*` to avoid accidentally including the `screenshots/` directory.

## Conventions

- **Imports at top of file.** All `import` statements must be placed at the top of the file, never inline or inside functions.
- **Import modules, not classes.** Always use `import module` rather than `from module import Class`. Access symbols via the module name as namespace (e.g. `capture.CaptureMethod`, not `from capture import CaptureMethod`).
- **No Co-Authored-By in commits.** Do not include `Co-Authored-By` trailer in git commit messages.
