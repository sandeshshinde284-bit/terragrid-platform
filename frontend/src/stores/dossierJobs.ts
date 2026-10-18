import { defineStore } from 'pinia'
import { ref } from 'vue'
import { logError } from '../utils/logger'

// Background crisis-report jobs, one per incident. The request runs here, not
// inside a page component, so it keeps going while the user switches tabs or
// visits another screen. Pages read the job state and apply the result when it
// arrives.
export type DossierJobState = 'running' | 'done' | 'fallback' | 'error'

export interface DossierJob {
  state: DossierJobState
  startedAt: number
  message: string | null
  result: any | null
}

export const useDossierJobsStore = defineStore('dossierJobs', () => {
  const jobs = ref<Record<string, DossierJob>>({})

  function jobFor(incidentId: string): DossierJob | undefined {
    return jobs.value[incidentId]
  }

  async function start(incidentId: string): Promise<void> {
    if (jobs.value[incidentId]?.state === 'running') return
    jobs.value[incidentId] = { state: 'running', startedAt: Date.now(), message: null, result: null }

    const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    try {
      const res = await fetch(`${host}/api/v1/incidents/${incidentId}/deep-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (data.status === 'fallback') {
        jobs.value[incidentId] = { ...jobs.value[incidentId], state: 'fallback', message: 'AI analysis is unavailable right now. The last saved report is still shown.' }
      } else if (data.dossier) {
        jobs.value[incidentId] = { ...jobs.value[incidentId], state: 'done', message: null, result: data }
      } else {
        jobs.value[incidentId] = { ...jobs.value[incidentId], state: 'error', message: 'The AI response contained no report. The last saved report is still shown.' }
      }
    } catch (err) {
      logError('Could not generate the deep AI dossier for this incident', err)
      jobs.value[incidentId] = { ...jobs.value[incidentId], state: 'error', message: 'Could not generate the report. The last saved report is still shown.' }
    }
  }

  return { jobs, jobFor, start }
})
