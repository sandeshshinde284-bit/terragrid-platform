import { inject } from 'vue'
import { logger as defaultLogger } from '@/config/logger'
import type { LogLevel } from '@/config/logger'

interface LogContext {
  [key: string]: any
}

export const useLogger = (componentName: string = 'Component') => {
  const log = inject<typeof defaultLogger>('logger', defaultLogger)

  return {
    debug: (message: string, context?: LogContext): void => {
      log.debug(message, { component: componentName, ...context })
    },
    info: (message: string, context?: LogContext): void => {
      log.info(message, { component: componentName, ...context })
    },
    warn: (message: string, context?: LogContext): void => {
      log.warn(message, { component: componentName, ...context })
    },
    error: (message: string, error?: Error | LogContext, context?: LogContext): void => {
      log.error(message, error instanceof Error ? error : { ...error, ...context }, context)
    },
  }
}