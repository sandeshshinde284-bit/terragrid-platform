import { App } from 'vue'
import { logger } from '@/config/logger'

export const loggerPlugin = {
  install(app: App): void {
    // Make logger available globally
    app.config.globalProperties.$log = logger

    // Provide for injection
    app.provide('logger', logger)

    // Log app lifecycle
    logger.info('TerraGrid Application Initialized')
  },
}

// Add TypeScript augmentation
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $log: typeof logger
  }
}