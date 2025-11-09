'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { API_URL } from '@/lib/config';
import {
  Folder,
  Zap,
  Plug,
  MessageSquare,
  TrendingUp,
  Plus,
  ChevronRight,
  Activity,
  Database,
  BarChart3
} from 'lucide-react';
// Dynamic import for heavy chart library
import dynamicImport from 'next/dynamic';

// Lazy load chart components
const ChartsComponent = dynamicImport(
  () => import('@/components/DashboardCharts'),
  {
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    ),
    ssr: false
  }
);

export const dynamic = 'force-dynamic';

// TypeScript interfaces
interface DashboardStats {
  total_projects: number;
  active_workflows: number;
  connected_integrations: number;
  ai_requests_today: number;
  ai_requests_week: number;
  total_databases: number;
  total_records: number;
}

interface ActivityItem {
  id: number;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  icon: string;
}

interface ChartDataPoint {
  date?: string;
  requests?: number;
  model?: string;
  workflow?: string;
  executions?: number;
  [key: string]: string | number | undefined;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [aiRequestsChart, setAiRequestsChart] = useState<ChartDataPoint[]>([]);
  const [modelUsageChart, setModelUsageChart] = useState<ChartDataPoint[]>([]);
  const [workflowStatsChart, setWorkflowStatsChart] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Auth token now comes from httpOnly cookies
      // Fetch stats
      const statsRes = await fetch(`${API_URL}/api/dashboard/stats`, {
        credentials: 'include'
      });
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch activity feed
      const activityRes = await fetch(`${API_URL}/api/dashboard/activity?limit=20`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (activityRes.ok) {
        const activityData = await activityRes.json();
        setActivity(activityData);
      }

      // Fetch chart data
      const aiChartRes = await fetch(`${API_URL}/api/dashboard/charts/ai-requests?days=7`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (aiChartRes.ok) {
        const aiChartData = await aiChartRes.json();
        setAiRequestsChart(aiChartData.data || []);
      }

      const modelChartRes = await fetch(`${API_URL}/api/dashboard/charts/model-usage`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (modelChartRes.ok) {
        const modelChartData = await modelChartRes.json();
        setModelUsageChart(modelChartData.data || []);
      }

      const workflowChartRes = await fetch(`${API_URL}/api/dashboard/charts/workflow-stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (workflowChartRes.ok) {
        const workflowChartData = await workflowChartRes.json();
        setWorkflowStatsChart(workflowChartData.data || []);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const createProject = async () => {
    if (!newProjectName.trim()) return;

    try {
      // Auth token now comes from httpOnly cookies
      const response = await fetch(`${API_URL}/api/projects`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newProjectName,
          description: newProjectDescription
        })
      });

      if (response.ok) {
        setShowNewProjectModal(false);
        setNewProjectName('');
        setNewProjectDescription('');
        fetchDashboardData(); // Refresh data
      }
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const formatRelativeTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays}d ago`;
  };

  const getActivityIcon = (iconName: string) => {
    const icons: { [key: string]: React.ReactNode } = {
      'Folder': <Folder className="w-4 h-4" />,
      'Zap': <Zap className="w-4 h-4" />,
      'Plug': <Plug className="w-4 h-4" />,
      'MessageSquare': <MessageSquare className="w-4 h-4" />,
      'Database': <Database className="w-4 h-4" />
    };
    return icons[iconName] || <Activity className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        {/* Loading Skeletons */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-gray-800 rounded-xl p-6 animate-pulse">
              <div className="h-12 bg-gray-700 rounded mb-4"></div>
              <div className="h-8 bg-gray-700 rounded w-20"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }


  return (
    <div className="p-6 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Projects"
          value={stats?.total_projects || 0}
          icon={<Folder className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="Active Workflows"
          value={stats?.active_workflows || 0}
          icon={<Zap className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="Connected Integrations"
          value={stats?.connected_integrations || 0}
          icon={<Plug className="w-6 h-6" />}
          color="green"
        />
        <StatCard
          title="AI Requests Today"
          value={stats?.ai_requests_today || 0}
          icon={<MessageSquare className="w-6 h-6" />}
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-xl p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => setShowNewProjectModal(true)}
            className="flex items-center gap-3 p-4 bg-blue-600/10 border border-blue-600/30 rounded-lg hover:bg-blue-600/20 transition-colors group"
          >
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Plus className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <div className="text-white font-medium">New Project</div>
              <div className="text-sm text-gray-400">Create a project</div>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 ml-auto group-hover:text-white transition-colors" />
          </button>

          <Link
            href="/workflows"
            className="flex items-center gap-3 p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg hover:bg-purple-600/20 transition-colors group"
          >
            <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <div className="text-white font-medium">New Workflow</div>
              <div className="text-sm text-gray-400">Create automation</div>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 ml-auto group-hover:text-white transition-colors" />
          </Link>

          <Link
            href="/integrations"
            className="flex items-center gap-3 p-4 bg-green-600/10 border border-green-600/30 rounded-lg hover:bg-green-600/20 transition-colors group"
          >
            <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
              <Plug className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <div className="text-white font-medium">Connect Integration</div>
              <div className="text-sm text-gray-400">Add service</div>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 ml-auto group-hover:text-white transition-colors" />
          </Link>

          <Link
            href="/chat"
            className="flex items-center gap-3 p-4 bg-orange-600/10 border border-orange-600/30 rounded-lg hover:bg-orange-600/20 transition-colors group"
          >
            <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div className="text-left">
              <div className="text-white font-medium">Start Chat</div>
              <div className="text-sm text-gray-400">Talk to AI</div>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 ml-auto group-hover:text-white transition-colors" />
          </Link>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity Feed */}
        <div className="lg:col-span-2 bg-gray-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Recent Activity
            </h2>
          </div>

          <div className="space-y-3">
            {activity.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                No recent activity
              </div>
            ) : (
              activity.map((item) => (
                <div
                  key={`${item.type}-${item.id}`}
                  className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center flex-shrink-0 text-gray-300">
                    {getActivityIcon(item.icon)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white text-sm font-medium truncate">
                      {item.title}
                    </div>
                    <div className="text-gray-400 text-xs">
                      {item.description}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 flex-shrink-0">
                    {formatRelativeTime(item.timestamp)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Secondary Stats */}
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Statistics</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-400">
                  <Database className="w-4 h-4" />
                  <span className="text-sm">Databases</span>
                </div>
                <span className="text-white font-semibold">{stats?.total_databases || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-400">
                  <Activity className="w-4 h-4" />
                  <span className="text-sm">Total Records</span>
                </div>
                <span className="text-white font-semibold">{stats?.total_records || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-400">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm">AI Requests (Week)</span>
                </div>
                <span className="text-white font-semibold">{stats?.ai_requests_week || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section - Lazy Loaded */}
      <ChartsComponent
        aiRequestsData={aiRequestsChart}
        modelUsageData={modelUsageChart}
        workflowStatsData={workflowStatsChart}
      />

      {/* New Project Modal */}
      {showNewProjectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold text-white mb-4">Create New Project</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Project Name</label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="My Awesome Project"
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Description (Optional)</label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  placeholder="What is this project about?"
                  rows={3}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={createProject}
                  disabled={!newProjectName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Project
                </button>
                <button
                  onClick={() => {
                    setShowNewProjectModal(false);
                    setNewProjectName('');
                    setNewProjectDescription('');
                  }}
                  className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'from-blue-600 to-blue-700',
    purple: 'from-purple-600 to-purple-700',
    green: 'from-green-600 to-green-700',
    orange: 'from-orange-600 to-orange-700'
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-all hover:scale-105">
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-400">{title}</div>
        <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center text-white`}>
          {icon}
        </div>
      </div>
      <div className="text-4xl font-bold text-white">{value.toLocaleString()}</div>
    </div>
  );
}
