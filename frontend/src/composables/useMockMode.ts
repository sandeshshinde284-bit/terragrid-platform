/**
 * Composable for mock/live data mode.
 *
 * There is no manual UI toggle. Mock vs. live is driven entirely by the
 * backend's USE_MOCK_DATA setting: App.vue fetches GET /api/v1/config on
 * load, which returns `mock_mode_enabled: settings.USE_MOCK_DATA`, and
 * stores it in appStore.isBackendMockModeEnabled. This composable just
 * exposes that single source of truth to components.
 *
 * To switch modes, set USE_MOCK_DATA on the backend (Cloud Run env var,
 * or .env locally) and restart/redeploy the backend - the frontend will
 * pick it up automatically on next load.
 */
import { computed } from 'vue'
import { useAppStore } from '@/stores'

export function useMockMode() {
  const appStore = useAppStore()

  /**
   * Current mock mode status, sourced from the backend's USE_MOCK_DATA config.
   */
  const isMockMode = computed(() => appStore.isBackendMockModeEnabled)

  /**
   * Get query parameter for API calls
   */
  const getMockParam = () => {
    return isMockMode.value ? '?use_mock=true' : ''
  }

  /**
   * Fetch with automatic mock mode handling
   */
  const fetchWithMockMode = async (url: string, options = {}) => {
    const separator = url.includes('?') ? '&' : '?'
    const mockParam = isMockMode.value ? `${separator}use_mock=true` : ''

    return fetch(url + mockParam, options)
  }

  return {
    isMockMode,
    getMockParam,
    fetchWithMockMode
  }
}