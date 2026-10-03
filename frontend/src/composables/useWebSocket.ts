import { ref, onUnmounted, onMounted } from 'vue'
import { useEventsStore } from '@/stores'

export function useWebSocket() {
  const eventsStore = useEventsStore()
  
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  let ws: WebSocket | null = null
  let pingInterval: number | null = null
  
  const connect = () => {
    // Connect to WebSocket using the current host, changing protocol to ws/wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // For local dev, hardcode the backend port to 8000
    const host = process.env.NODE_ENV === 'production' 
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
            console.log('✅ Connection confirmed by server')
            break
            
          case 'pong':
            // Heartbeat received
            break
            
          case 'incidents_polled':
            console.log(`📢 Real-time update received: ${message.data.total_events} events`)
            
            // Only update store if there are actual changes
            if (message.data.changes.new > 0 || message.data.changes.updated > 0 || message.data.changes.removed > 0) {
                // Update the Pinia store with the fresh real-time data
                // In a production app you might merge changes, here we just replace with the top 50
                eventsStore.setIncidents(message.data.events)
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
      
      attemptReconnect()
    }

    ws.onerror = (error) => {
      console.error('❌ WebSocket Error:', error)
      // The onclose event will fire immediately after onerror, triggering reconnect
    }
  }

  const attemptReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.error('⛔ Max WebSocket reconnection attempts reached. Please refresh the page.')
      return
    }
    
    reconnectAttempts.value++
    
    // Exponential backoff: 2s, 4s, 8s, 16s...
    const timeout = Math.pow(2, reconnectAttempts.value) * 1000
    console.log(`⏳ Attempting to reconnect in ${timeout/1000}s (Attempt ${reconnectAttempts.value}/${maxReconnectAttempts})...`)
    
    setTimeout(() => {
      connect()
    }, timeout)
  }

  const disconnect = () => {
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
