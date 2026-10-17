// One short, readable label for an incident's canonical id.
//
// The backend's canonical id is "event_<db id>" (see ingest + GET /incidents).
// Showing that raw string everywhere is noisy, so screens display "EVT-<n>".
// The label is derived from the id, never invented: it is the same event on
// every screen. Ids that don't match the canonical pattern are shown as-is.
export const displayIncidentId = (id: string | null | undefined): string => {
  if (!id) return '—'
  const m = /^event_(\d+)$/.exec(id)
  return m ? `EVT-${m[1]}` : id
}
