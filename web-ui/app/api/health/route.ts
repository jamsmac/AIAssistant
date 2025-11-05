/**
 * Health Check Endpoint
 * Returns system health status for monitoring
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  environment: string;
  services: {
    api: boolean;
    database: boolean;
    cache?: boolean;
    storage?: boolean;
  };
  metrics?: {
    uptime: number;
    responseTime: number;
    memoryUsage: number;
    cpuUsage?: number;
  };
  errors?: string[];
}

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  const errors: string[] = [];
  let dbHealthy = false;

  // Check database connectivity
  try {
    if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
      );

      // Simple query to check database connection
      const { error } = await supabase.from('blog_posts').select('id').limit(1);

      if (error) {
        errors.push(`Database error: ${error.message}`);
      } else {
        dbHealthy = true;
      }
    } else {
      errors.push('Database configuration missing');
    }
  } catch (error) {
    errors.push(`Database connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }

  // Calculate metrics
  const memoryUsage = process.memoryUsage();
  const uptime = process.uptime();
  const responseTime = Date.now() - startTime;

  // Determine overall status
  let status: 'healthy' | 'degraded' | 'unhealthy' = 'healthy';
  if (errors.length > 0 || !dbHealthy) {
    status = dbHealthy ? 'degraded' : 'unhealthy';
  }

  const healthStatus: HealthStatus = {
    status,
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
    services: {
      api: true,
      database: dbHealthy,
      cache: true, // Add Redis check if using cache
      storage: true, // Add S3/storage check if using
    },
    metrics: {
      uptime: Math.floor(uptime),
      responseTime,
      memoryUsage: Math.round(memoryUsage.heapUsed / 1024 / 1024), // MB
    },
  };

  if (errors.length > 0) {
    healthStatus.errors = errors;
  }

  // Return appropriate status code
  const statusCode = status === 'healthy' ? 200 : status === 'degraded' ? 200 : 503;

  return NextResponse.json(healthStatus, { status: statusCode });
}

// Database-specific health check
export async function POST(request: NextRequest) {
  const startTime = Date.now();
  const checks: Record<string, boolean | string> = {};

  try {
    // Parse request body for specific checks
    const body = await request.json();
    const { detailed = false } = body;

    if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
      const supabase = createClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
      );

      // Check tables exist
      const tables = ['blog_posts', 'blog_authors', 'fractal_agents'];
      for (const table of tables) {
        try {
          const { error } = await supabase.from(table).select('count', { count: 'exact', head: true });
          checks[`table_${table}`] = !error;
        } catch {
          checks[`table_${table}`] = false;
        }
      }

      // Check write capability (if detailed)
      if (detailed) {
        try {
          const testData = {
            event_type: 'health_check',
            event_action: 'test',
            timestamp: new Date().toISOString(),
          };

          const { error: writeError } = await supabase.from('audit_logs').insert(testData);
          checks.write_capability = !writeError;

          // Clean up test data
          if (!writeError) {
            await supabase
              .from('audit_logs')
              .delete()
              .eq('event_type', 'health_check')
              .eq('event_action', 'test');
          }
        } catch {
          checks.write_capability = false;
        }
      }
    }

    const allHealthy = Object.values(checks).every((check) => check === true);
    const responseTime = Date.now() - startTime;

    return NextResponse.json(
      {
        status: allHealthy ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        responseTime,
        checks,
      },
      {
        status: allHealthy ? 200 : 503,
      }
    );
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        message: error instanceof Error ? error.message : 'Health check failed',
        timestamp: new Date().toISOString(),
      },
      {
        status: 500,
      }
    );
  }
}