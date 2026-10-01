/**
 * Composable for managing Mock/Live data mode
 * Stores preference in localStorage and syncs with backend
 */
import { ref, computed } from 'vue'

// Global mock mode state
const mockModeEnabled = ref(localStorage.getItem('mockMode') !== 'false')

export function useMockMode() {
  /**
   * Get current mock mode status
   */
  const isMockMode = computed(() => mockModeEnabled.value)

  /**
   * Toggle between mock and live data
   */
  const toggleMockMode = async () => {
    mockModeEnabled.value = !mockModeEnabled.value
    localStorage.setItem('mockMode', String(mockModeEnabled.value))

    // Sync with backend
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/config/mock-mode?enabled=${mockModeEnabled.value}`,
        { method: 'POST' }
      )
      const data = await response.json()
      console.log(`📡 Mock Mode: ${data.mode}`)
    } catch (error) {
      console.log('⚠️ Backend offline - using localStorage mock mode only')
    }
  }

  /**
   * Get query parameter for API calls
   */
  const getMockParam = () => {
    return mockModeEnabled.value ? '?use_mock=true' : ''
  }

  /**
   * Fetch with automatic mock mode handling
   */
  const fetchWithMockMode = async (url: string, options = {}) => {
    const separator = url.includes('?') ? '&' : '?'
    const mockParam = mockModeEnabled.value ? `${separator}use_mock=true` : ''
    
    return fetch(url + mockParam, options)
  }

  /**
   * Set mock mode explicitly
   */
  const setMockMode = (enabled: boolean) => {
    mockModeEnabled.value = enabled
    localStorage.setItem('mockMode', String(enabled))
  }

  return {
    isMockMode,
    toggleMockMode,
    getMockParam,
    fetchWithMockMode,
    setMockMode
  }
}
