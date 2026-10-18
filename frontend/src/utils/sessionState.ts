// Per-tab session state. It survives a page reload in the same tab and is
// cleared when the tab closes. A new tab starts fresh.
//
// Every access is wrapped in try/catch: private windows, blocked storage, or
// a full quota must never break the page. If storage is unavailable, the page
// simply starts from its defaults.

const KEY = 'terragrid.session.v1'

export const readSession = (): Record<string, any> => {
  try {
    return JSON.parse(sessionStorage.getItem(KEY) || '{}') || {}
  } catch {
    return {}
  }
}

export const writeSession = (patch: Record<string, unknown>): void => {
  try {
    sessionStorage.setItem(KEY, JSON.stringify({ ...readSession(), ...patch }))
  } catch {
    // Storage unavailable: keep working without persistence.
  }
}
