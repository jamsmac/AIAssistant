/**
 * Sentry Client Configuration
 *
 * This file configures Sentry for the browser/client-side.
 * It captures errors, performance data, and user feedback.
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || 'development'

Sentry.init({
  // Sentry DSN (Data Source Name) - get from Sentry dashboard
  dsn: SENTRY_DSN,

  // Environment name
  environment: ENVIRONMENT,

  // Adjust sample rate for production to avoid overloading Sentry
  // 1.0 = 100% of errors captured
  // 0.1 = 10% of errors captured
  tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,

  // Session Replay - captures user sessions for debugging
  // Only in production and for a subset of sessions
  replaysSessionSampleRate: ENVIRONMENT === 'production' ? 0.1 : 0,
  replaysOnErrorSampleRate: ENVIRONMENT === 'production' ? 1.0 : 0,

  // Integrations are automatically configured in Next.js SDK
  // Performance monitoring is enabled via tracesSampleRate

  // Before sending errors, you can modify or filter them
  beforeSend(event, hint) {
    // Don't send errors in development
    if (ENVIRONMENT === 'development') {
      console.error('Sentry Error (not sent):', hint.originalException || hint.syntheticException)
      return null
    }

    // Filter out known errors that are not actionable
    const error = hint.originalException
    if (error && typeof error === 'object' && 'message' in error) {
      const errorMessage = String(error.message)

      // Ignore common browser extension errors
      if (errorMessage.includes('ResizeObserver loop')) {
        return null
      }

      // Ignore network errors that are user's problem
      if (errorMessage.includes('Network request failed')) {
        return null
      }

      // Ignore cancelled requests
      if (errorMessage.includes('AbortError')) {
        return null
      }
    }

    return event
  },

  // Ignore specific errors
  ignoreErrors: [
    // Browser extensions
    'top.GLOBALS',
    'chrome-extension://',
    'moz-extension://',

    // Random plugins/extensions
    'ComcastInHomeStbSDK',
    'atomicFindClose',

    // Network errors
    'Network request failed',
    'NetworkError',
    'Failed to fetch',

    // Cancelled requests
    'AbortError',
    'cancelled',

    // ResizeObserver errors (not actionable)
    'ResizeObserver loop',
  ],

  // Don't report errors from these URLs
  denyUrls: [
    // Browser extensions
    /extensions\//i,
    /^chrome:\/\//i,
    /^moz-extension:\/\//i,

    // Facebook
    /graph\.facebook\.com/i,

    // Analytics
    /google-analytics\.com/i,
    /googletagmanager\.com/i,
  ],

  // Release tracking
  release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA,

  // Additional context
  initialScope: {
    tags: {
      runtime: 'browser',
    },
  },
})

// Export for manual error reporting
export { Sentry }
