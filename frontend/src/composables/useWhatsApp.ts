/**
 * Composable for the WhatsApp feature flag.
 *
 * There is no manual UI toggle. Whether any WhatsApp UI/functionality shows
 * at all is driven entirely by the backend's ENABLE_WHATSAPP setting (see
 * backend/config.py): App.vue fetches GET /api/v1/config on load, which
 * returns `whatsapp_enabled: settings.ENABLE_WHATSAPP`, and stores it in
 * appStore.isWhatsAppEnabled. This composable just exposes that single
 * source of truth to components.
 *
 * Off by default - WhatsApp's terms around unofficial/self-hosted clients
 * (WAHA) haven't been confirmed as compliant. The backend also enforces
 * this independently at the route level (backend/routes/prepare.py's
 * /alerts/send and /alerts/recipients), so hiding the UI here is a UX
 * convenience, not the only guard.
 *
 * To turn it on, set ENABLE_WHATSAPP=true on the backend (Cloud Run env
 * var, or .env locally) and restart/redeploy - the frontend picks it up
 * automatically on next load.
 */
import { computed } from 'vue'
import { useAppStore } from '@/stores'

export function useWhatsApp() {
  const appStore = useAppStore()

  const isWhatsAppEnabled = computed(() => appStore.isWhatsAppEnabled)

  return {
    isWhatsAppEnabled,
  }
}
