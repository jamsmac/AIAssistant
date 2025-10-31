import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  
  // Reduce bundle size
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  
  // Optimize for Vercel serverless functions
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Exclude large optional dependencies from serverless function
      config.externals = config.externals || [];
      config.externals.push({
        'sharp': 'commonjs sharp',
        'canvas': 'commonjs canvas',
        '@swc/core': 'commonjs @swc/core',
      });
    }
    
    // Optimize bundle
    config.optimization = {
      ...config.optimization,
      moduleIds: 'deterministic',
    };
    
    return config;
  },
};

export default nextConfig;
