/**
 * Security Configuration and Utilities
 */

/**
 * Content Security Policy Configuration
 */
export function getCSPHeader(): string {
  const isDev = process.env.NODE_ENV === 'development';

  const directives = [
    // Default source
    `default-src 'self'`,

    // Script sources
    `script-src 'self' ${isDev ? "'unsafe-inline' 'unsafe-eval'" : "'nonce-{NONCE}'"} https://cdn.jsdelivr.net`,

    // Style sources
    `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,

    // Image sources
    `img-src 'self' data: https: blob:`,

    // Font sources
    `font-src 'self' https://fonts.gstatic.com`,

    // Connect sources (API calls)
    `connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL} ${process.env.NEXT_PUBLIC_SUPABASE_URL} https://api.sentry.io wss://*.supabase.co`,

    // Frame ancestors (prevent clickjacking)
    `frame-ancestors 'none'`,

    // Base URI
    `base-uri 'self'`,

    // Form action
    `form-action 'self'`,

    // Upgrade insecure requests
    !isDev && `upgrade-insecure-requests`,

    // Report URI
    process.env.NEXT_PUBLIC_CSP_REPORT_URI && `report-uri ${process.env.NEXT_PUBLIC_CSP_REPORT_URI}`,
  ].filter(Boolean);

  return directives.join('; ');
}

/**
 * Security Headers Configuration
 */
export const securityHeaders = [
  {
    key: 'X-DNS-Prefetch-Control',
    value: 'on',
  },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  },
];

/**
 * Rate Limiting Configuration
 */
export const rateLimitConfig = {
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: {
    anonymous: 100,
    authenticated: 1000,
    api: 50,
  },
};

/**
 * CORS Configuration
 */
export function getCORSConfig() {
  const allowedOrigins = process.env.NEXT_PUBLIC_ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'];

  return {
    origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
      // Allow requests with no origin (like mobile apps)
      if (!origin) return callback(null, true);

      if (allowedOrigins.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    exposedHeaders: ['X-Total-Count', 'X-Page-Count'],
    maxAge: 86400, // 24 hours
  };
}

/**
 * Input Sanitization
 */
export function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags
    .replace(/on\w+\s*=\s*["'][^"']*["']/gi, '') // Remove inline event handlers
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '') // Remove iframes
    .replace(/javascript:/gi, ''); // Remove javascript: protocol
}

/**
 * SQL Injection Prevention
 */
export function escapeSQLInput(input: string): string {
  return input
    .replace(/'/g, "''") // Escape single quotes
    .replace(/\\/g, '\\\\') // Escape backslashes
    .replace(/"/g, '\\"') // Escape double quotes
    .replace(/\n/g, '\\n') // Escape newlines
    .replace(/\r/g, '\\r') // Escape carriage returns
    .replace(/\x00/g, '\\x00') // Escape null bytes
    .replace(/\x1a/g, '\\x1a'); // Escape EOF
}

/**
 * XSS Prevention
 */
export function escapeHTML(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
    '/': '&#x2F;',
  };

  return text.replace(/[&<>"'/]/g, (char) => map[char]);
}

/**
 * Password Strength Validation
 */
export function validatePasswordStrength(password: string): {
  isValid: boolean;
  errors: string[];
  strength: 'weak' | 'medium' | 'strong';
} {
  const errors: string[] = [];
  let strength: 'weak' | 'medium' | 'strong' = 'weak';
  let score = 0;

  // Minimum length
  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  } else {
    score++;
  }

  // Contains uppercase
  if (!/[A-Z]/.test(password)) {
    errors.push('Password should contain at least one uppercase letter');
  } else {
    score++;
  }

  // Contains lowercase
  if (!/[a-z]/.test(password)) {
    errors.push('Password should contain at least one lowercase letter');
  } else {
    score++;
  }

  // Contains number
  if (!/[0-9]/.test(password)) {
    errors.push('Password should contain at least one number');
  } else {
    score++;
  }

  // Contains special character
  if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) {
    errors.push('Password should contain at least one special character');
  } else {
    score++;
  }

  // Determine strength
  if (score >= 5) strength = 'strong';
  else if (score >= 3) strength = 'medium';

  return {
    isValid: errors.length === 0,
    errors,
    strength,
  };
}

/**
 * JWT Token Validation
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= exp;
  } catch {
    return true; // If parsing fails, consider token expired
  }
}

/**
 * Generate Nonce for CSP
 */
export function generateNonce(): string {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

/**
 * Validate Email Format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate URL Format
 */
export function isValidURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Sensitive Data Masking
 */
export function maskSensitiveData(data: string, type: 'email' | 'phone' | 'credit-card' | 'api-key'): string {
  switch (type) {
    case 'email':
      const [user, domain] = data.split('@');
      if (!domain) return '***';
      return `${user.substring(0, 2)}***@${domain}`;

    case 'phone':
      return data.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2');

    case 'credit-card':
      return data.replace(/(\d{4})\d{8}(\d{4})/, '$1********$2');

    case 'api-key':
      return `${data.substring(0, 8)}...${data.substring(data.length - 4)}`;

    default:
      return '***';
  }
}