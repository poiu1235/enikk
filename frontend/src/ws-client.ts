/**
 * WebSocket JSON-RPC client for Enikk daemon.
 *
 * Protocol:
 *   Client → { id, method, params }
 *   Server → { id, result }          (response to request)
 *   Server → { type, ... }           (async event broadcast)
 */

export interface WsEvent {
  type: string
  runId?: string
  text?: string
  content?: string
  error?: string
  [key: string]: unknown
}

export interface WsResult {
  id: number | string
  result: Record<string, unknown>
}

export interface WsClientOptions {
  url?: string
  onEvent?: (event: WsEvent) => void
  onConnected?: () => void
  onDisconnected?: () => void
}

const DEFAULT_URL = 'ws://127.0.0.1:18932'

export class WsClient {
  private ws: WebSocket | null = null
  private url: string
  private nextId = 1
  private pending = new Map<number | string, {
    resolve: (r: unknown) => void
    reject: (e: Error) => void
  }>()
  private onEvent?: (event: WsEvent) => void
  onConnected?: () => void
  onDisconnected?: () => void
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private _connected = false

  constructor(options: WsClientOptions = {}) {
    this.url = options.url || DEFAULT_URL
    this.onEvent = options.onEvent
    this.onConnected = options.onConnected
    this.onDisconnected = options.onDisconnected
  }

  get connected() {
    return this._connected
  }

  connect() {
    if (this.ws) return

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this._connected = true
      this.onConnected?.()
    }

    this.ws.onclose = () => {
      this._connected = false
      this.onDisconnected?.()
      // Reject all pending requests
      for (const [, { reject }] of this.pending) {
        reject(new Error('WebSocket disconnected'))
      }
      this.pending.clear()
      // Auto-reconnect after 2s
      this.reconnectTimer = setTimeout(() => {
        this.ws = null
        this.connect()
      }, 2000)
    }

    this.ws.onmessage = (ev: MessageEvent) => {
      try {
        const msg = JSON.parse(ev.data)
        if ('type' in msg) {
          // Async event broadcast
          this.onEvent?.(msg as WsEvent)
        } else if ('result' in msg || 'error' in msg) {
          // Response to a request
          const id = msg.id
          const p = this.pending.get(id)
          if (p) {
            this.pending.delete(id)
            if ('error' in msg) {
              p.reject(new Error(msg.error?.message || String(msg.error)))
            } else {
              p.resolve(msg.result)
            }
          }
        }
      } catch {
        // Ignore malformed messages
      }
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this._connected = false
  }

  private request(method: string, params: Record<string, unknown> = {}): Promise<unknown> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket not connected'))
        return
      }
      const id = this.nextId++
      this.pending.set(id, { resolve, reject })
      this.ws.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }))
    })
  }

  // ── RPC methods ──

  chatSend(content: string) {
    return this.request('chat.send', { content }) as Promise<{ runId: string; status: string }>
  }

  chatAbort(runId: string) {
    return this.request('chat.abort', { runId }) as Promise<{ status: string }>
  }

  chatHistory() {
    return this.request('chat.history') as Promise<{ count: number; messages: unknown[] }>
  }

  screenshot() {
    return this.request('screenshot') as Promise<Record<string, unknown>>
  }

  click(x: number, y: number, target?: string, reason?: string) {
    return this.request('click', { x, y, target: target || '', reason: reason || '' }) as Promise<Record<string, unknown>>
  }
}
