/**
 * Sentry Edge Configuration
 *
 * This file configures Sentry for Edge Runtime (middleware, edge functions).
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || 'development'

Sentry.init({
  dsn: SENTRY_DSN,
  environment: ENVIRONMENT,
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,

  beforeSend(event) {
    // Don't send in development
    if (ENVIRONMENT === 'development') {
      return null
    }
    return event
  },

  release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,

  initialScope: {
    tags: {
      runtime: 'edge',
    },
  },
})

export { Sentry }
