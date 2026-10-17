import { ref, onUnmounted, onMounted } from 'vue'
import { useEventsStore } from '@/stores'
import countriesData from '@/data/countries.json' with { type: 'json' }
import { logFeature, logWarn, logError } from '@/utils/logger'
import { impactMetricsFrom } from '@/utils/impactMetrics'

export function useWebSocket() {
  const eventsStore = useEventsStore()
  
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  let ws: WebSocket | null = null
  let pingInterval: number | null = null
  let isDestroyed = false

  /**
   * Resolve country code from location name using same logic as Dashboard
   * Supports: "City, Country Code" or alias resolution
   */
  const resolveCountryCode = (locationName: string): string => {
    if (!locationName) return 'UN'
    
    const aliases = countriesData.aliases || {}
    
    // Strategy 1: Extract last comma-separated part if it looks like a code
    const parts = locationName.split(',')
    if (parts.length > 1) {
      const potential = parts[parts.length - 1].trim()
      if (potential && potential.length <= 3 && /^[A-Z]{2,3}$/.test(potential)) {
        return potential
      }
    }
    
    // Strategy 2: Check aliases (case-insensitive)
    const upper = locationName.toUpperCase().trim()
    if (aliases[upper as keyof typeof aliases]) {
      return aliases[upper as keyof typeof aliases]
    }
    
    // Strategy 3: Return UN for unknown
    return 'UN'
  }
  
  const connect = () => {
    // Connect to WebSocket using the current host, changing protocol to ws/wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // For local dev, hardcode the backend port to 8000
    // Use VITE_API_URL if provided (stripping http/https), otherwise fallback to origin
    let host = window.location.host;
    if (import.meta.env.VITE_API_URL) {
      host = import.meta.env.VITE_API_URL.replace(/^https?:\/\//, '');
    } else if (import.meta.env.MODE !== 'production') {
      host = 'localhost:8000';
    }
    const wsUrl = `${protocol}//${host}/ws/dashboard`
    
    logFeature('dashboard_websocket', 'info', { action: 'connecting', url: wsUrl })
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      logFeature('dashboard_websocket', 'success', { action: 'connected' })
      isConnected.value = true
      reconnectAttempts.value = 0
      
      // Keep WebSocket alive even if tab is inactive
      // Use short 15s ping to prevent browser idle timeout
      // (Prevents automatic disconnect when user switches tabs)
      pingInterval = window.setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 15000)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        
        switch (message.type) {
          case 'connection_established':
            logFeature('dashboard_websocket', 'info', { action: 'server_confirmed' })
            break
            
          case 'pong':
            // Heartbeat received
            break
            
          case 'incidents_polled':
            logFeature('dashboard_websocket', 'info', { action: 'update_received', total_events: message.data.total_events })
            
            // Only update store if there are actual changes
            if (message.data.changes.new > 0 || message.data.changes.updated > 0 || message.data.changes.removed > 0) {
                // Transform WebSocket events to IncidentLevel1 format (consistent with Dashboard)
                const transformedEvents = message.data.events.map((event: any, index: number) => {
                  const impact = event.data?.impact || event.impact || {}
                  const locationName = event.location_name || event.location || 'Unknown'
                  const severity = (event.severity || 'medium').toLowerCase()
                  const source = event.source || event.data?.source || 'unknown'
                  
                  // Use consistent country code resolution (matches Dashboard logic)
                  const countryCode = resolveCountryCode(locationName)
                  
                  // Preserve original ID if available, else use canonical format
                  const originalId = event.data?.id || event.data?.nasa_id || event.data?.gdacs_id || event.id
                  const resolvedId = originalId ? String(originalId) : `event_${event.id || index + 1}`
                  
                  return {
                    id: resolvedId,
                    type: event.event_type || 'other',
                    location: locationName,
                    countryCode: countryCode,
                    severity: (severity === 'critical' ? 'high' : severity) as 'low' | 'medium' | 'high',
                    status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
                    ...impactMetricsFrom({ ...event, impact }),
                    detectionTime: new Date(event.event_timestamp || event.created_at || Date.now()),
                    coordinates: [event.latitude || 0, event.longitude || 0] as [number, number],
                    source: source,
                    confidence: event.confidence || event.data?.confidence || 0,
                    event_timestamp: event.event_timestamp || event.created_at || Date.now(),
                    data: event.data || {},
                  }
                })
                // ⚠️ CRITICAL: mergeMode=true prevents DATA LOSS
                // If we used mergeMode=false (default), we'd replace ALL 100 incidents 
                // loaded on page-open with just the top 5 from this broadcast,
                // losing 95 incidents from the dashboard!
                // mergeMode=true does an UPSERT: only updates the top 5 by ID,
                // keeping all other 95 incidents intact on the dashboard.
                eventsStore.setIncidents(transformedEvents, true)
            }
            break
            
          default:
            logWarn(`Received a WebSocket message type the dashboard doesn't handle: ${message.type}`)
        }
      } catch (err) {
        logError('Could not parse an incoming WebSocket message as JSON', err)
      }
    }

    ws.onclose = (event) => {
      logFeature('dashboard_websocket', 'warning', { action: 'disconnected', close_code: event.code })
      isConnected.value = false
      if (pingInterval) clearInterval(pingInterval)

      if (!isDestroyed) {
          attemptReconnect()
      }
    }

    ws.onerror = (error) => {
      logError('WebSocket connection error (a disconnect event will follow and trigger reconnect)', error)
    }
  }

  const attemptReconnect = () => {
    if (isDestroyed) return
    
    reconnectAttempts.value++
    
    // Limit reconnect attempts to 5 to avoid spamming
    if (reconnectAttempts.value > maxReconnectAttempts) {
      logFeature('dashboard_websocket', 'error', { action: 'reconnect_abandoned', attempts: maxReconnectAttempts })
      isConnected.value = false
      return
    }

    // Exponential backoff with cap: 2s, 4s, 8s, 16s, 30s, 30s...
    const backoffMs = Math.min(Math.pow(2, reconnectAttempts.value) * 1000, 30000)
    logFeature('dashboard_websocket', 'warning', { action: 'reconnecting', delay_seconds: backoffMs / 1000, attempt: reconnectAttempts.value, max_attempts: maxReconnectAttempts })
    
    setTimeout(() => {
      if (!isDestroyed) {
          connect()
      }
    }, backoffMs)
  }

  const disconnect = () => {
    isDestroyed = true // Set flag to prevent reconnect loop
    if (ws) {
      ws.close(1000, 'Component unmounted')
    }
    if (pingInterval) {
      clearInterval(pingInterval)
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    isConnected,
    reconnectAttempts,
    connect,
    disconnect
  }
}
