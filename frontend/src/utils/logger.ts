/**
 * Structured console + file logging, mirroring the backend's
 * [FEATURE_HEALTH] convention (see backend/services/*.py).
 *
 * Every call does two things:
 *   1. Writes to the browser console as before (so dev tools still work).
 *   2. Fires a background POST to the backend, which appends the same line
 *      to logs/frontend/frontend.log (see backend/routes/client_logs.py) -
 *      so frontend issues show up on disk next to the backend's own
 *      logs/backend/backend.log instead of only existing in a browser tab
 *      nobody is watching.
 *
 * The POST is fire-and-forget: it never awaits, never throws into the
 * caller, and never logs its own failure (that would risk a feedback loop
 * if the backend itself is down). A page the user never opened dev tools
 * on still gets its errors on disk; a backend that's unreachable just means
 * the console-only path still works exactly as before.
 *
 * Usage:
 *   import { logFeature, logInfo, logWarn, logError } from '@/utils/logger'
 *
 *   logFeature('incidents_fetch', 'success', { count: events.length })
 *   logFeature('incidents_fetch', 'error', { error: String(err) })
 *   logWarn('Falling back to cached incidents after a failed hydrate request', err)
 */

export type FeatureStatus = 'success' | 'error' | 'warning' | 'fallback' | 'info'

function backendHost(): string {
  const envUrl = (import.meta as any).env?.VITE_API_URL
  if (envUrl) return envUrl
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000'
  }
  return typeof window !== 'undefined' ? window.location.origin : ''
}

/** Fire-and-forget: ship one log line to logs/frontend/frontend.log. Never throws, never retried. */
function shipToBackend(level: 'info' | 'warn' | 'error', message: string): void {
  try {
    const host = backendHost()
    if (!host) return
    fetch(`${host}/api/v1/client-logs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level,
        message,
        url: typeof window !== 'undefined' ? window.location.pathname : undefined,
        client_time: new Date().toISOString(),
      }),
      keepalive: true, // lets the request finish even if the user navigates away
    }).catch(() => {
      // Backend unreachable - the console line above already has it, and
      // we deliberately don't log this failure (would risk a logging loop).
    })
  } catch {
    // Same reasoning - swallow and move on, logging must never break the UI.
  }
}

/**
 * Logs one line in the same grep-able shape as the backend's
 * [FEATURE_HEALTH] lines: feature=<name> status=<status> key=value ...
 */
export function logFeature(
  feature: string,
  status: FeatureStatus,
  details?: Record<string, unknown>,
): void {
  const detailText = details
    ? ' ' + Object.entries(details)
        .map(([key, value]) => `${key}=${value}`)
        .join(' ')
    : ''
  const line = `[FEATURE_HEALTH] feature=${feature} status=${status}${detailText}`

  if (status === 'error') {
    console.error(line)
    shipToBackend('error', line)
  } else if (status === 'warning' || status === 'fallback') {
    console.warn(line)
    shipToBackend('warn', line)
  } else {
    console.info(line)
    shipToBackend('info', line)
  }
}

/** Plain informational message - use for routine lifecycle events (connected, loaded, etc). */
export function logInfo(message: string): void {
  console.info(message)
  shipToBackend('info', message)
}

/** A degraded-but-handled condition - a fallback path was taken, a retry is happening, etc. */
export function logWarn(message: string, err?: unknown): void {
  if (err !== undefined) {
    console.warn(message, err)
    shipToBackend('warn', `${message} - ${String(err)}`)
  } else {
    console.warn(message)
    shipToBackend('warn', message)
  }
}

/** A real failure - a request that didn't succeed and wasn't recovered from. */
export function logError(message: string, err?: unknown): void {
  if (err !== undefined) {
    console.error(message, err)
    shipToBackend('error', `${message} - ${String(err)}`)
  } else {
    console.error(message)
    shipToBackend('error', message)
  }
}
