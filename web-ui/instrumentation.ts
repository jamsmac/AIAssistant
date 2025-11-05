/**
 * Next.js Instrumentation
 *
 * This file is automatically loaded by Next.js when the server starts.
 * It's used to initialize monitoring and tracing tools like Sentry.
 */

export async function register() {
  // Only run on the server
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    await import('./sentry.server.config')
  }

  // Edge runtime
  if (process.env.NEXT_RUNTIME === 'edge') {
    await import('./sentry.edge.config')
  }
}
