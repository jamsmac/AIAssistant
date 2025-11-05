/**
 * Production Deployment Configuration
 */

module.exports = {
  // Deployment Target
  target: 'vercel', // or 'aws', 'gcp', 'azure', 'docker'

  // Build Configuration
  build: {
    command: 'npm run build',
    outputDirectory: '.next',
    environment: 'production',
    optimizations: {
      minify: true,
      treeshake: true,
      splitChunks: true,
      compressImages: true,
      generateSourceMaps: false, // Disable in production for security
    },
  },

  // Environment Variables (keys only, values from platform)
  env: {
    required: [
      'NEXT_PUBLIC_API_URL',
      'NEXT_PUBLIC_SUPABASE_URL',
      'NEXT_PUBLIC_SUPABASE_ANON_KEY',
      'DATABASE_URL',
      'JWT_SECRET',
    ],
    optional: [
      'NEXT_PUBLIC_SENTRY_DSN',
      'SENTRY_AUTH_TOKEN',
      'NEXT_PUBLIC_GA_TRACKING_ID',
    ],
  },

  // Health Checks
  healthChecks: {
    endpoints: [
      {
        path: '/api/health',
        expectedStatus: 200,
        timeout: 5000,
      },
      {
        path: '/api/health/db',
        expectedStatus: 200,
        timeout: 10000,
      },
    ],
    interval: 30000, // 30 seconds
    retries: 3,
  },

  // Scaling Configuration
  scaling: {
    minInstances: 2,
    maxInstances: 10,
    targetCPU: 70, // percentage
    targetMemory: 80, // percentage
    scaleDownDelay: 300, // seconds
    scaleUpDelay: 60, // seconds
  },

  // CDN Configuration
  cdn: {
    enabled: true,
    provider: 'cloudflare', // or 'cloudfront', 'fastly'
    cacheControl: {
      static: 'public, max-age=31536000, immutable', // 1 year
      images: 'public, max-age=86400, stale-while-revalidate=604800', // 1 day, stale 1 week
      api: 'no-cache, no-store, must-revalidate',
      html: 'public, max-age=0, must-revalidate',
    },
    compression: ['gzip', 'br'], // Brotli and Gzip
  },

  // Database Configuration
  database: {
    poolMin: 2,
    poolMax: 10,
    connectionTimeout: 60000, // 1 minute
    idleTimeout: 10000, // 10 seconds
    ssl: {
      required: true,
      rejectUnauthorized: true,
    },
  },

  // Monitoring & Alerts
  monitoring: {
    sentry: {
      enabled: true,
      tracesSampleRate: 0.1, // 10% in production
      environment: 'production',
    },
    logging: {
      level: 'info',
      format: 'json',
      destination: 'stdout',
    },
    alerts: {
      errorRate: {
        threshold: 5, // percentage
        window: 300, // seconds
        action: 'email,slack',
      },
      responseTime: {
        threshold: 1000, // milliseconds
        window: 300, // seconds
        action: 'slack',
      },
      availability: {
        threshold: 99.5, // percentage
        window: 3600, // 1 hour
        action: 'email,slack,pagerduty',
      },
    },
  },

  // Security Configuration
  security: {
    rateLimit: {
      windowMs: 900000, // 15 minutes
      max: 100, // requests per window per IP
      message: 'Too many requests, please try again later',
    },
    cors: {
      origins: process.env.NEXT_PUBLIC_ALLOWED_ORIGINS?.split(',') || [],
      credentials: true,
    },
    helmet: {
      contentSecurityPolicy: true,
      crossOriginEmbedderPolicy: true,
      crossOriginOpenerPolicy: true,
      crossOriginResourcePolicy: true,
      dnsPrefetchControl: true,
      frameguard: true,
      hidePoweredBy: true,
      hsts: true,
      ieNoOpen: true,
      noSniff: true,
      originAgentCluster: true,
      permittedCrossDomainPolicies: false,
      referrerPolicy: true,
      xssFilter: true,
    },
  },

  // Backup Configuration
  backup: {
    database: {
      enabled: true,
      schedule: '0 2 * * *', // Daily at 2 AM
      retention: 30, // days
      location: 's3://your-backup-bucket/db',
    },
    files: {
      enabled: true,
      schedule: '0 3 * * 0', // Weekly on Sunday at 3 AM
      retention: 7, // days
      location: 's3://your-backup-bucket/files',
    },
  },

  // Deployment Stages
  stages: {
    preview: {
      branch: 'develop',
      autoDeployment: true,
      protection: false,
    },
    staging: {
      branch: 'staging',
      autoDeployment: true,
      protection: true,
      approvers: ['team-lead', 'devops'],
    },
    production: {
      branch: 'main',
      autoDeployment: false,
      protection: true,
      approvers: ['team-lead', 'devops', 'product-owner'],
      preDeploymentChecks: [
        'tests-passing',
        'security-scan',
        'performance-benchmark',
      ],
    },
  },

  // Post-Deployment Actions
  postDeploy: {
    warmup: {
      enabled: true,
      endpoints: ['/', '/api/health', '/dashboard'],
      concurrency: 5,
    },
    notifications: {
      slack: {
        webhook: process.env.SLACK_WEBHOOK_URL,
        channel: '#deployments',
        mentions: ['@devops'],
      },
      email: {
        recipients: ['team@example.com'],
        subject: 'Production Deployment Completed',
      },
    },
    smokeTests: {
      enabled: true,
      timeout: 60000, // 1 minute
      scripts: ['npm run test:e2e:smoke'],
    },
  },

  // Rollback Configuration
  rollback: {
    automatic: {
      enabled: true,
      triggers: {
        errorRateThreshold: 10, // percentage
        responseTimeThreshold: 2000, // milliseconds
        availabilityThreshold: 95, // percentage
      },
      window: 600, // 10 minutes after deployment
    },
    manual: {
      enabled: true,
      retainVersions: 5,
    },
  },
};