import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,

  // Reduce bundle size
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },

  // Use Turbopack (Next.js 16 default)
  turbopack: {
    // Explicitly set root to current directory
    root: process.cwd(),
  },
};

export default nextConfig;
