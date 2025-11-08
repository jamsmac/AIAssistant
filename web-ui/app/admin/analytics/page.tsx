"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface SystemStats {
  agents: {
    total: number;
    active: number;
    total_tasks: number;
    successful_tasks: number;
    avg_success_rate: number;
  };
  blog: {
    total_posts: number;
    published: number;
    drafts: number;
    total_views: number;
    total_likes: number;
    avg_reading_time: number;
  };
  performance: {
    avg_response_time: number;
    uptime_hours: number;
    errors_last_24h: number;
  };
}

interface AgentPerformance {
  name: string;
  agent_type: string;
  success_rate: number;
  total_tasks: number;
  avg_confidence: number;
}

interface TopPost {
  title: string;
  slug: string;
  view_count: number;
  like_count: number;
  published_at: string;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [topAgents, setTopAgents] = useState<AgentPerformance[]>([]);
  const [topPosts, setTopPosts] = useState<TopPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // Fetch system stats
      const statsRes = await fetch('/api/fractal/system-status');
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch top agents
      const agentsRes = await fetch('/api/fractal/agents');
      if (agentsRes.ok) {
        const agentsData = await agentsRes.json();
        const agents = agentsData.agents || [];
        const sorted = agents
          .map((a: any) => ({
            name: a.name,
            agent_type: a.agent_type,
            success_rate: a.total_tasks_processed > 0 
              ? (a.successful_tasks / a.total_tasks_processed) * 100 
              : 0,
            total_tasks: a.total_tasks_processed,
            avg_confidence: a.avg_confidence_score * 100
          }))
          .sort((a: any, b: any) => b.success_rate - a.success_rate)
          .slice(0, 5);
        setTopAgents(sorted);
      }

      // Fetch top posts
      const postsRes = await fetch('/api/blog/posts?status=published');
      if (postsRes.ok) {
        const postsData = await postsRes.json();
        const posts = postsData.posts || [];
        const sorted = posts
          .sort((a: any, b: any) => b.view_count - a.view_count)
          .slice(0, 5);
        setTopPosts(sorted);
      }
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-4 gap-6">
              {[1,2,3,4].map(i => <div key={i} className="h-32 bg-gray-200 rounded"></div>)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-gray-600 mt-1">System performance and insights</p>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Total Agents</span>
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 text-lg">🤖</span>
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.agents.total || 0}</p>
            <p className="text-xs text-green-600 mt-1">
              {stats?.agents.active || 0} active
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Tasks Completed</span>
              <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 text-lg">✓</span>
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.agents.total_tasks || 0}</p>
            <p className="text-xs text-green-600 mt-1">
              {stats?.agents.avg_success_rate?.toFixed(1) || 0}% success rate
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Published Posts</span>
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-purple-600 text-lg">📝</span>
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.blog.published || 0}</p>
            <p className="text-xs text-gray-600 mt-1">
              {stats?.blog.total_posts || 0} total posts
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Total Views</span>
              <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 text-lg">👁️</span>
              </div>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.blog.total_views || 0}</p>
            <p className="text-xs text-red-600 mt-1">
              {stats?.blog.total_likes || 0} likes
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Top Performing Agents */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Top Performing Agents</h2>
              <Link href="/fractal-agents" className="text-sm text-blue-600 hover:underline">
                View all →
              </Link>
            </div>
            {topAgents.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No agent data available</p>
            ) : (
              <div className="space-y-4">
                {topAgents.map((agent, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{agent.name}</p>
                      <p className="text-xs text-gray-500 capitalize">{agent.agent_type}</p>
                    </div>
                    <div className="text-right mr-4">
                      <p className="text-sm font-medium text-gray-900">{agent.total_tasks} tasks</p>
                      <p className="text-xs text-gray-500">{agent.avg_confidence.toFixed(0)}% confidence</p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-600">
                        {agent.success_rate.toFixed(1)}%
                      </div>
                      <p className="text-xs text-gray-500">success</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Top Blog Posts */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Top Blog Posts</h2>
              <Link href="/blog" className="text-sm text-blue-600 hover:underline">
                View all →
              </Link>
            </div>
            {topPosts.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No posts available</p>
            ) : (
              <div className="space-y-4">
                {topPosts.map((post, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                    <Link href={`/blog/${post.slug}`} className="font-medium text-gray-900 hover:text-blue-600">
                      {post.title}
                    </Link>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>👁️ {post.view_count} views</span>
                      <span>❤️ {post.like_count} likes</span>
                      <span>{new Date(post.published_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* System Performance */}
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <h2 className="text-xl font-bold mb-6">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
              <p className="text-sm text-blue-600 font-medium mb-2">Agent Success Rate</p>
              <p className="text-4xl font-bold text-blue-900">
                {stats?.agents.avg_success_rate?.toFixed(1) || 0}%
              </p>
              <div className="mt-4 h-2 bg-blue-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-600 rounded-full"
                  style={{ width: `${stats?.agents.avg_success_rate || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
              <p className="text-sm text-green-600 font-medium mb-2">Blog Engagement</p>
              <p className="text-4xl font-bold text-green-900">
                {stats?.blog.total_views || 0}
              </p>
              <p className="text-sm text-green-700 mt-2">
                Total views across all posts
              </p>
            </div>

            <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
              <p className="text-sm text-purple-600 font-medium mb-2">Content Published</p>
              <p className="text-4xl font-bold text-purple-900">
                {stats?.blog.published || 0}
              </p>
              <p className="text-sm text-purple-700 mt-2">
                {stats?.blog.drafts || 0} drafts pending
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
          <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link href="/admin/blog/new" className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-center transition-colors">
              <p className="text-2xl mb-2">📝</p>
              <p className="font-medium">Create Post</p>
            </Link>
            <Link href="/fractal-agents" className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-center transition-colors">
              <p className="text-2xl mb-2">🤖</p>
              <p className="font-medium">View Agents</p>
            </Link>
            <Link href="/admin/blog" className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-center transition-colors">
              <p className="text-2xl mb-2">📊</p>
              <p className="font-medium">Manage Posts</p>
            </Link>
            <Link href="/blog" className="bg-white/20 hover:bg-white/30 rounded-lg p-4 text-center transition-colors">
              <p className="text-2xl mb-2">🌐</p>
              <p className="font-medium">View Blog</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
