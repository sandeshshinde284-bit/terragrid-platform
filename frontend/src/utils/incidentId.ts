// Human-readable incident label, e.g. "FLD-IN-0042" (flood, India, record 42).
//
// Built only from the event's own fields: its type, its country code, and the
// database number inside its canonical id ("event_<n>"). The number is unique,
// so two events never get the same label, even if they share type and country.
// Ids that don't match the canonical pattern are shown as-is.

type IncidentLike = { id: string; type?: string; countryCode?: string | null }

const TYPE_CODES: Record<string, string> = {
  flood: 'FLD',
  earthquake: 'EQK',
  seismic: 'EQK',
  fire: 'FIR',
  wildfire: 'FIR',
  storm: 'STM',
  hurricane: 'STM',
  cyclone: 'STM',
  typhoon: 'STM',
  volcano: 'VOL',
  landslide: 'LSD',
  weather: 'WX',
}

const typeCode = (type?: string): string => {
  if (!type) return 'INC'
  const key = type.toLowerCase()
  return TYPE_CODES[key] ?? key.replace(/[^a-z]/g, '').slice(0, 3).toUpperCase().padEnd(3, 'X')
}

const countryCodeOf = (cc?: string | null): string => {
  if (!cc || cc === 'UN') return 'XX'
  return cc.toUpperCase().slice(0, 2)
}

export const displayIncidentId = (incident: IncidentLike | string | null | undefined): string => {
  if (!incident) return '—'
  const inc: IncidentLike = typeof incident === 'string' ? { id: incident } : incident
  const m = /^event_(\d+)$/.exec(inc.id)
  if (!m) return inc.id
  const number = m[1].padStart(4, '0')
  return `${typeCode(inc.type)}-${countryCodeOf(inc.countryCode)}-${number}`
}
