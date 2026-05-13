# Enikk Web Dashboard

Vue 3 + Vite + TypeScript embedded dashboard for the Enikk daemon.

## Development

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
```

Output goes to `dist/` and is served by the Enikk WebSocket daemon.

## Architecture

```
┌─────────────────────┐         WebSocket (JSON-RPC)         ┌──────────────────┐
│  Vue 3 SPA (browser) │ ◀────────────────────────────────────▶ │  ws-daemon       │
│  ChatPanel + Pinia   │         ws://127.0.0.1:18932         │  AgentManager    │
└─────────────────────┘                                       └──────────────────┘
```

## Protocol

| Method | Params | Description |
|--------|--------|-------------|
| `chat.send` | `{ content }` | Start agent conversation |
| `chat.abort` | `{ runId }` | Interrupt agent |
| `chat.history` | — | Get conversation history |
| `screenshot` | — | On-demand screenshot + analysis |
| `click` | `{ x, y, target?, reason? }` | Click at normalized coordinates |
