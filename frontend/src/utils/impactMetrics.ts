// Real-or-nothing impact metrics.
//
// The backend's impact analysis is the only source for these numbers. When it
// has no value for an incident, the value stays `null` and the UI shows a dash
// ("—"). Earlier code filled gaps with invented defaults (150 km², 50,000
// people, 5.2 km²/h, a 31.2 km² forecast, a threat score of 50), which made
// unknown incidents look measured. Do not add fallback numbers here.

export type Metric = number | null

const isNumber = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)

/** First value that is a real finite number, otherwise null. */
export const pickNumber = (...candidates: unknown[]): Metric => {
  for (const c of candidates) {
    if (isNumber(c)) return c
  }
  return null
}

/** Pull the five impact metrics from one incident, preferring backend impact fields. */
export const impactMetricsFrom = (event: any): {
  threatScore: Metric
  affectedArea: Metric
  affectedPopulation: Metric
  trend: Metric
  forecast6h: Metric
} => {
  const impact = event?.impact || {}
  return {
    threatScore: pickNumber(impact.risk_score, event?.threatScore),
    affectedArea: pickNumber(impact.affected_area_km2, event?.affectedArea),
    affectedPopulation: pickNumber(impact.affected_population, event?.affectedPopulation),
    trend: pickNumber(impact.trend_km2_per_hour, event?.trend),
    forecast6h: pickNumber(impact.forecast_6h_km2, event?.forecast6h),
  }
}

export const DASH = '—'

/** Format a number with fixed decimals and a unit, or a dash when unknown. */
export const fmtFixed = (v: Metric, digits = 0, suffix = ''): string =>
  v === null ? DASH : `${v.toFixed(digits)}${suffix}`

/** Format a count with thousands separators, or a dash when unknown. */
export const fmtCount = (v: Metric): string =>
  v === null ? DASH : v.toLocaleString()

/** Format a population as e.g. "120K", or a dash when unknown. */
export const fmtThousands = (v: Metric): string =>
  v === null ? DASH : `${(v / 1000).toFixed(0)}K`

/** Sum only the known values; unknown incidents do not add to totals. */
export const sumKnown = (values: Metric[]): number =>
  values.reduce<number>((sum, v) => (v === null ? sum : sum + v), 0)

/** Signed change, e.g. "+3.2 km²/h", or a dash when unknown. */
export const fmtSigned = (v: Metric, digits = 1, suffix = ''): string =>
  v === null ? DASH : `${v >= 0 ? '+' : ''}${v.toFixed(digits)}${suffix}`
