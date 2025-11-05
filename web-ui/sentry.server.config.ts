/**
 * Sentry Server Configuration
 *
 * This file configures Sentry for the server/backend (API routes, SSR).
 * It captures server-side errors and performance data.
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || 'development'

Sentry.init({
  // Sentry DSN
  dsn: SENTRY_DSN,

  // Environment
  environment: ENVIRONMENT,

  // Server-side performance monitoring
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,

  // Integrations are automatically configured in Next.js SDK
  // HTTP tracking and profiling are enabled automatically

  // Before sending errors
  beforeSend(event, hint) {
    // Don't send in development
    if (ENVIRONMENT === 'development') {
      console.error('Sentry Server Error (not sent):', hint.originalException || hint.syntheticException)
      return null
    }

    // Add server context
    if (event.request) {
      event.tags = {
        ...event.tags,
        server: 'nextjs',
        route: event.request.url,
      }
    }

    return event
  },

  // Ignore specific errors
  ignoreErrors: [
    // Expected errors
    'ECONNREFUSED',
    'ETIMEDOUT',
    'ENOTFOUND',
    'AbortError',

    // Database connection errors (handled elsewhere)
    'Connection terminated',
    'Connection lost',
  ],

  // Release tracking
  release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,

  // Additional context
  initialScope: {
    tags: {
      runtime: 'nodejs',
    },
  },
})

// Export for manual error reporting
export { Sentry }
