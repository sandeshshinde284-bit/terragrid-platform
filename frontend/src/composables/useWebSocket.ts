import { ref, onUnmounted, onMounted } from 'vue'
import { useEventsStore } from '@/stores'
import countriesData from '@/data/countries.json' with { type: 'json' }

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
    const host = import.meta.env.MODE === 'production' 
      ? window.location.host 
      : 'localhost:8000'
      
    const wsUrl = `${protocol}//${host}/ws/dashboard`
    
    console.log(`📡 Attempting WebSocket connection to ${wsUrl}`)
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('🟢 WebSocket Connected')
      isConnected.value = true
      reconnectAttempts.value = 0
      
      // Start 30 second ping heartbeat to keep connection alive
      pingInterval = window.setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        }
      }, 30000)
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        
        switch (message.type) {
          case 'connection_established':
            console.log(' Connection confirmed by server')
            break
            
          case 'pong':
            // Heartbeat received
            break
            
          case 'incidents_polled':
            console.log(`📢 Real-time update received: ${message.data.total_events} events`)
            
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
                    threatScore: impact.risk_score ?? 50,
                    detectionTime: new Date(event.event_timestamp || event.created_at || Date.now()),
                    affectedArea: impact.affected_area_km2 ?? 0,
                    affectedPopulation: impact.affected_population ?? 0,
                    trend: impact.trend_km2_per_hour ?? 0,
                    forecast6h: impact.forecast_6h_km2 ?? 0,
                    coordinates: [event.latitude || 0, event.longitude || 0] as [number, number],
                  }
                })
                eventsStore.setIncidents(transformedEvents)
            }
            break
            
          default:
            console.log('Unknown message type received:', message.type)
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }

    ws.onclose = (event) => {
      console.log('🔴 WebSocket Disconnected', event.code)
      isConnected.value = false
      if (pingInterval) clearInterval(pingInterval)
      
      if (!isDestroyed) {
          attemptReconnect()
      }
    }

    ws.onerror = (error) => {
      console.error(' WebSocket Error:', error)
      // The onclose event will fire immediately after onerror, triggering reconnect
    }
  }

  const attemptReconnect = () => {
    if (isDestroyed || reconnectAttempts.value >= maxReconnectAttempts) {
      if (!isDestroyed) {
        console.error(' Max WebSocket reconnection attempts reached. Please refresh the page.')
      }
      return
    }
    
    reconnectAttempts.value++
    
    // Exponential backoff: 2s, 4s, 8s, 16s...
    const timeout = Math.pow(2, reconnectAttempts.value) * 1000
    console.log(`Attempting to reconnect in ${timeout/1000}s (Attempt ${reconnectAttempts.value}/${maxReconnectAttempts})...`)
    
    setTimeout(() => {
      if (!isDestroyed) {
          connect()
      }
    }, timeout)
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
