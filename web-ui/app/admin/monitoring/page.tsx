/**
 * System Monitoring Dashboard
 * Real-time health, performance, and error tracking
 */

'use client';

import { useState, useEffect } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  Globe,
  HardDrive,
  RefreshCw,
  Server,
  TrendingDown,
  TrendingUp,
  Users,
  Zap,
  AlertTriangle,
  BarChart3,
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: number;
  services: {
    api: boolean;
    database: boolean;
    cache: boolean;
    storage: boolean;
  };
  metrics: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  };
  errors: {
    last24h: number;
    last7d: number;
    trend: number;
  };
}

interface PerformanceMetrics {
  responseTime: {
    p50: number;
    p95: number;
    p99: number;
  };
  throughput: number;
  errorRate: number;
  saturation: number;
}

export default function MonitoringDashboard() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');

  // Mock data - replace with real API calls
  const [responseTimeData] = useState([
    { time: '00:00', p50: 45, p95: 120, p99: 250 },
    { time: '04:00', p50: 42, p95: 115, p99: 240 },
    { time: '08:00', p50: 55, p95: 145, p99: 290 },
    { time: '12:00', p50: 65, p95: 165, p99: 320 },
    { time: '16:00', p50: 58, p95: 150, p99: 300 },
    { time: '20:00', p50: 48, p95: 125, p99: 260 },
  ]);

  const [throughputData] = useState([
    { time: '00:00', requests: 1200 },
    { time: '04:00', requests: 800 },
    { time: '08:00', requests: 2500 },
    { time: '12:00', requests: 3200 },
    { time: '16:00', requests: 2800 },
    { time: '20:00', requests: 1500 },
  ]);

  const [errorsByType] = useState([
    { type: '4xx', count: 145, color: '#fbbf24' },
    { type: '5xx', count: 23, color: '#ef4444' },
    { type: 'Network', count: 8, color: '#8b5cf6' },
    { type: 'Timeout', count: 12, color: '#3b82f6' },
  ]);

  const [serviceStatus] = useState([
    { name: 'API Gateway', status: 'healthy', uptime: 99.99, responseTime: 45 },
    { name: 'Database Primary', status: 'healthy', uptime: 99.95, responseTime: 12 },
    { name: 'Database Replica', status: 'healthy', uptime: 99.94, responseTime: 15 },
    { name: 'Redis Cache', status: 'healthy', uptime: 100, responseTime: 2 },
    { name: 'CDN', status: 'healthy', uptime: 100, responseTime: 8 },
    { name: 'Worker Queue', status: 'degraded', uptime: 98.5, responseTime: 125 },
  ]);

  useEffect(() => {
    // Fetch initial data
    fetchHealth();
    fetchPerformance();

    // Auto-refresh
    const interval = autoRefresh ? setInterval(() => {
      fetchHealth();
      fetchPerformance();
    }, 30000) : null; // 30 seconds

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchHealth = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();

      // Mock enhanced data
      setHealth({
        status: data.status || 'healthy',
        uptime: data.metrics?.uptime || 864000,
        services: data.services || {
          api: true,
          database: true,
          cache: true,
          storage: true,
        },
        metrics: {
          cpu: Math.random() * 100,
          memory: Math.random() * 100,
          disk: Math.random() * 100,
          network: Math.random() * 100,
        },
        errors: {
          last24h: 188,
          last7d: 1245,
          trend: -12.5,
        },
      });
    } catch (error) {
      console.error('Failed to fetch health:', error);
    }
  };

  const fetchPerformance = async () => {
    // Mock performance data
    setPerformance({
      responseTime: {
        p50: 45 + Math.random() * 10,
        p95: 120 + Math.random() * 30,
        p99: 250 + Math.random() * 50,
      },
      throughput: 2500 + Math.random() * 500,
      errorRate: 0.5 + Math.random() * 0.3,
      saturation: 65 + Math.random() * 20,
    });
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchHealth(), fetchPerformance()]);
    setTimeout(() => setRefreshing(false), 500);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'unhealthy':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500/10';
      case 'degraded':
        return 'bg-yellow-500/10';
      case 'unhealthy':
        return 'bg-red-500/10';
      default:
        return 'bg-gray-500/10';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}d ${hours}h`;
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Activity className="w-8 h-8 text-blue-500" />
              System Monitoring
            </h1>
            <p className="text-gray-600 mt-2">Real-time health and performance monitoring</p>
          </div>

          <div className="flex items-center gap-4">
            {/* Time Range Selector */}
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>

            {/* Auto Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                autoRefresh ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
              Auto Refresh
            </button>

            {/* Manual Refresh */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {/* Overall Health */}
        <div className={`bg-white p-6 rounded-xl shadow-sm border ${health?.status === 'healthy' ? 'border-green-200' : health?.status === 'degraded' ? 'border-yellow-200' : 'border-red-200'}`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">System Health</h3>
            {health?.status === 'healthy' ? (
              <CheckCircle2 className="w-6 h-6 text-green-500" />
            ) : health?.status === 'degraded' ? (
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
            ) : (
              <AlertCircle className="w-6 h-6 text-red-500" />
            )}
          </div>
          <p className={`text-2xl font-bold ${getStatusColor(health?.status || '')}`}>
            {health?.status?.toUpperCase()}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Uptime: {health ? formatUptime(health.uptime) : '-'}
          </p>
        </div>

        {/* Response Time */}
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">Response Time</h3>
            <Zap className="w-6 h-6 text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performance?.responseTime.p50.toFixed(0)}ms
          </p>
          <p className="text-sm text-gray-500 mt-2">
            P95: {performance?.responseTime.p95.toFixed(0)}ms
          </p>
        </div>

        {/* Throughput */}
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">Throughput</h3>
            <BarChart3 className="w-6 h-6 text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performance?.throughput.toFixed(0)} req/s
          </p>
          <p className="text-sm text-gray-500 mt-2">
            {((performance?.throughput || 0) * 60).toFixed(0)} req/min
          </p>
        </div>

        {/* Error Rate */}
        <div className="bg-white p-6 rounded-xl shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-700">Error Rate</h3>
            <AlertCircle className="w-6 h-6 text-red-500" />
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performance?.errorRate.toFixed(2)}%
          </p>
          <div className="flex items-center gap-1 mt-2">
            {health?.errors.trend && health.errors.trend < 0 ? (
              <>
                <TrendingDown className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-500">{Math.abs(health.errors.trend)}%</span>
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4 text-red-500" />
                <span className="text-sm text-red-500">{health?.errors.trend}%</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Service Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {serviceStatus.map((service) => (
            <div
              key={service.name}
              className={`p-4 rounded-lg border ${getStatusBg(service.status)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-700">{service.name}</span>
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    service.status === 'healthy'
                      ? 'bg-green-100 text-green-700'
                      : service.status === 'degraded'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-red-100 text-red-700'
                  }`}
                >
                  {service.status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Uptime:</span>
                  <span className="ml-1 font-medium">{service.uptime}%</span>
                </div>
                <div>
                  <span className="text-gray-500">Latency:</span>
                  <span className="ml-1 font-medium">{service.responseTime}ms</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Response Time Chart */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Response Time Percentiles</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={responseTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="p50" stroke="#10b981" name="P50" strokeWidth={2} />
              <Line type="monotone" dataKey="p95" stroke="#f59e0b" name="P95" strokeWidth={2} />
              <Line type="monotone" dataKey="p99" stroke="#ef4444" name="P99" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Throughput Chart */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Request Throughput</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={throughputData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="requests" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Resource Usage and Error Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Resource Usage */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Resource Usage</h2>
          <div className="space-y-4">
            {[
              { label: 'CPU', value: health?.metrics.cpu || 0, icon: Cpu, color: 'blue' },
              { label: 'Memory', value: health?.metrics.memory || 0, icon: Server, color: 'green' },
              { label: 'Disk', value: health?.metrics.disk || 0, icon: HardDrive, color: 'purple' },
              { label: 'Network', value: health?.metrics.network || 0, icon: Globe, color: 'orange' },
            ].map((resource) => (
              <div key={resource.label}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <resource.icon className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">{resource.label}</span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{resource.value.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full bg-${resource.color}-500`}
                    style={{ width: `${resource.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Error Distribution */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Error Distribution</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={errorsByType}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="count"
              >
                {errorsByType.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {errorsByType.map((error) => (
              <div key={error.type} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: error.color }} />
                <span className="text-sm text-gray-600">
                  {error.type}: {error.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alert Panel */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Active Alerts</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">High Worker Queue Latency</p>
              <p className="text-sm text-gray-600 mt-1">
                Worker queue response time is above threshold (125ms)
              </p>
              <p className="text-xs text-gray-500 mt-2">Triggered 15 minutes ago</p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-gray-900">Traffic Spike Detected</p>
              <p className="text-sm text-gray-600 mt-1">
                Request volume increased by 45% in the last hour
              </p>
              <p className="text-xs text-gray-500 mt-2">Informational - 1 hour ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}