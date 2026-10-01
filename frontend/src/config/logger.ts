import pino from 'pino'

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

interface LogContext {
  component?: string
  [key: string]: any
}

class Logger {
  private logger: pino.Logger
  private logLevel: LogLevel

  constructor(logLevel: LogLevel = 'info') {
    this.logLevel = logLevel
    this.logger = pino({
      level: logLevel,
      browser: {
        asObject: true,
        colorize: true,
      },
      transport: {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'SYS:standard',
          ignore: 'pid,hostname',
          singleLine: false,
        },
      },
    })
  }

  public debug(message: string, context?: LogContext): void {
    this.logger.debug({ ...context }, message)
  }

  public info(message: string, context?: LogContext): void {
    this.logger.info({ ...context }, message)
  }

  public warn(message: string, context?: LogContext): void {
    this.logger.warn({ ...context }, message)
  }

  public error(message: string, error?: Error | LogContext, context?: LogContext): void {
    if (error instanceof Error) {
      this.logger.error({ ...context, error: error.message, stack: error.stack }, message)
    } else {
      this.logger.error({ ...error }, message)
    }
  }

  public setLevel(level: LogLevel): void {
    this.logLevel = level
    this.logger.level = level
  }

  public getLevel(): LogLevel {
    return this.logLevel
  }
}

// Create singleton instance
const logLevel = (import.meta.env.VITE_LOG_LEVEL as LogLevel) || 'info'
export const logger = new Logger(logLevel)

export default logger