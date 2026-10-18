// Rule-based next step: shown on the Incidents list before any AI analysis.
// It is a rule, not an AI output, and it says which rule applied.
// Thresholds live here only. Change them in one place.

export const EVACUATION_THRESHOLD = 80
export const SHELTER_THRESHOLD = 65

export interface RuleNextStep {
  title: string
  basis: string
}

export const ruleBasedNextStep = (incident: { type?: string | null; threatScore?: number | null }): RuleNextStep => {
  const score = incident.threatScore
  if (score === null || score === undefined) {
    return { title: 'Awaiting risk score', basis: 'No risk score yet' }
  }
  if (score >= EVACUATION_THRESHOLD) {
    return { title: 'Assess evacuation needs', basis: `Rule: risk ${score}/100, at or above ${EVACUATION_THRESHOLD}` }
  }
  if ((incident.type || '').toLowerCase() === 'flood') {
    return { title: 'Assess shelter readiness', basis: `Rule: flood, risk ${score}/100` }
  }
  if (score >= SHELTER_THRESHOLD) {
    return { title: 'Prepare shelters and first responders', basis: `Rule: risk ${score}/100, at or above ${SHELTER_THRESHOLD}` }
  }
  return { title: 'Review response readiness', basis: `Rule: risk ${score}/100, below ${SHELTER_THRESHOLD}` }
}
