'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Document {
  id: string;
  name: string;
  type: string;
  source_type: string;
  source_url: string | null;
  status: string;
  error_message: string | null;
  processing_started_at: string | null;
  processing_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface Stats {
  total_documents: number;
  completed_analyses: number;
  total_endpoints: number;
  total_schemas: number;
}

export default function DocumentAnalyzerDashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_documents: 0,
    completed_analyses: 0,
    total_endpoints: 0,
    total_schemas: 0
  });
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('');

  useEffect(() => {
    fetchDocuments();
    fetchStats();
  }, [filterStatus]);

  const fetchDocuments = async () => {
    try {
      let url = '/api/doc-analyzer/documents';
      if (filterStatus) {
        url += `?status=${filterStatus}`;
      }

      const res = await fetch(url);
      const data = await res.json();
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/doc-analyzer/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const deleteDocument = async (docId: string, docName: string) => {
    if (!confirm(`Delete "${docName}"? This will also delete all analysis results.`)) {
      return;
    }

    try {
      const res = await fetch(`/api/doc-analyzer/documents/${docId}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        fetchDocuments();
        fetchStats();
      }
    } catch (error) {
      alert('Failed to delete document: ' + error);
    }
  };

  const triggerAnalysis = async (docId: string) => {
    try {
      const res = await fetch(`/api/doc-analyzer/documents/${docId}/analyze`, {
        method: 'POST'
      });

      if (res.ok) {
        alert('Analysis started! Refresh the page in a moment to see results.');
        setTimeout(fetchDocuments, 2000);
      }
    } catch (error) {
      alert('Failed to trigger analysis: ' + error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'openapi':
      case 'swagger':
        return '📋';
      case 'pdf':
        return '📄';
      case 'google_sheets':
        return '📊';
      default:
        return '📚';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📚 Documentation Analyzer</h1>
              <p className="text-sm text-gray-600">AI-powered API documentation analysis</p>
            </div>
            <Link
              href="/admin/doc-analyzer/new"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              + Analyze Documentation
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Total Documents</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_documents}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Completed</div>
            <div className="text-2xl font-bold text-green-600">{stats.completed_analyses}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Total Endpoints</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total_endpoints}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600">Total Schemas</div>
            <div className="text-2xl font-bold text-purple-600">{stats.total_schemas}</div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">Filter by status:</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-1 border rounded-lg"
            >
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>

            {filterStatus && (
              <button
                onClick={() => setFilterStatus('')}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear filter
              </button>
            )}
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📚</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No documents analyzed yet</h3>
              <p className="text-gray-600 mb-4">Upload your first API documentation to get started</p>
              <Link
                href="/admin/doc-analyzer/new"
                className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                + Analyze Documentation
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Document</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <span className="text-2xl mr-3">{getTypeIcon(doc.type)}</span>
                          <div>
                            <div className="font-medium text-gray-900">{doc.name}</div>
                            {doc.error_message && (
                              <div className="text-xs text-red-600 mt-1">Error: {doc.error_message}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded capitalize">
                          {doc.type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {doc.source_url ? (
                          <a
                            href={doc.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:text-blue-800"
                          >
                            {new URL(doc.source_url).hostname}
                          </a>
                        ) : (
                          <span className="text-sm text-gray-500">Uploaded file</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(doc.status)}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right text-sm">
                        <div className="flex justify-end gap-2">
                          {doc.status === 'completed' && (
                            <Link
                              href={`/admin/doc-analyzer/${doc.id}`}
                              className="px-3 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                            >
                              View
                            </Link>
                          )}
                          {doc.status === 'pending' && (
                            <button
                              onClick={() => triggerAnalysis(doc.id)}
                              className="px-3 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100"
                            >
                              Analyze
                            </button>
                          )}
                          {doc.status === 'failed' && (
                            <button
                              onClick={() => triggerAnalysis(doc.id)}
                              className="px-3 py-1 bg-yellow-50 text-yellow-700 rounded hover:bg-yellow-100"
                            >
                              Retry
                            </button>
                          )}
                          <button
                            onClick={() => deleteDocument(doc.id, doc.name)}
                            className="px-3 py-1 bg-red-50 text-red-700 rounded hover:bg-red-100"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
