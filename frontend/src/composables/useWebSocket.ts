import { ref, onUnmounted, onMounted } from 'vue'
import { useEventsStore } from '@/stores'

export function useWebSocket() {
  const eventsStore = useEventsStore()
  
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  let ws: WebSocket | null = null
  let pingInterval: number | null = null
  let isDestroyed = false // Flag to prevent reconnect loops on unmount
  
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
                // Update the Pinia store with the fresh real-time data
                // Transform the raw backend DB events into the IncidentLevel1 format expected by the frontend
                const transformedEvents = message.data.events.map((e: any) => {
                  const impact = e.data?.impact || e.impact || {}
                  
                  return {
                    id: String(e.id || e.data?.id || `inc-${Math.random()}`),
                    type: e.event_type || 'other',
                    location: e.location_name || 'Unknown',
                    countryCode: e.data?.countryCode || 'UN',
                    severity: e.severity || 'medium',
                    status: e.status || 'active',
                    threatScore: impact.risk_score || 50,
                    detectionTime: new Date(e.event_timestamp || e.created_at || Date.now()),
                    affectedArea: impact.affected_area_km2 || 0,
                    affectedPopulation: impact.affected_population || 0,
                    trend: impact.trend_km2_per_hour || 0,
                    forecast6h: impact.forecast_6h_km2 || 0,
                    coordinates: [e.latitude, e.longitude] as [number, number],
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
