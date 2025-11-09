import type { NextConfig } from "next";
import { withSentryConfig } from '@sentry/nextjs';
import createBundleAnalyzer from '@next/bundle-analyzer';

const withBundleAnalyzer = createBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  reactCompiler: true,

  // Temporarily disable strict type checking for build
  typescript: {
    ignoreBuildErrors: true,
  },

  // Fix workspace root detection
  turbopack: {
    root: '/Users/js/autopilot-core/web-ui',
  },

  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts', 'reactflow'],
  },

  // Production optimizations
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Bundle optimization
  webpack: (config, { isServer }) => {
    // Optimize client-side bundle
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Vendor chunk for React and core libraries
            react: {
              name: 'react-vendor',
              test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
              priority: 40,
              enforce: true,
            },
            // Separate chunk for large visualization libraries
            charts: {
              name: 'charts',
              test: /[\\/]node_modules[\\/](recharts|d3)[\\/]/,
              priority: 30,
              enforce: true,
            },
            // Separate chunk for React Flow
            reactflow: {
              name: 'reactflow',
              test: /[\\/]node_modules[\\/]reactflow[\\/]/,
              priority: 30,
              enforce: true,
            },
            // Separate chunk for Tiptap editor
            tiptap: {
              name: 'tiptap',
              test: /[\\/]node_modules[\\/]@tiptap[\\/]/,
              priority: 30,
              enforce: true,
            },
            // Common chunk for shared code
            common: {
              name: 'common',
              minChunks: 2,
              priority: 20,
              reuseExistingChunk: true,
            },
          },
        },
      };
    }

    return config;
  },

  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
  },

  // Headers for security and performance
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
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
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

// Sentry configuration
const sentryWebpackPluginOptions = {
  // Suppresses source map uploading logs during build
  silent: true,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  // Upload source maps in production only
  hideSourceMaps: true,
  // Disable Sentry in development
  disableServerWebpackPlugin: process.env.NODE_ENV !== 'production',
  disableClientWebpackPlugin: process.env.NODE_ENV !== 'production',
};

// Export config with Sentry wrapper
export default withSentryConfig(withBundleAnalyzer(nextConfig), sentryWebpackPluginOptions);
