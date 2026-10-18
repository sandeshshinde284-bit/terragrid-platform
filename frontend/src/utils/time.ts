// Server timestamps are stored as naive UTC. Without a timezone marker,
// browsers read them as local time, which shifts every elapsed time.
export const parseServerTime = (value: unknown): Date | null => {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return isNaN(value.getTime()) ? null : value
  if (typeof value !== 'string') return null
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(value)
  const d = new Date(hasZone ? value : `${value}Z`)
  return isNaN(d.getTime()) ? null : d
}
