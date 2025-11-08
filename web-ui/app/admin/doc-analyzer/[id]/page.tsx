'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

interface AnalysisData {
  doc_source_id: string;
  status: string;
  summary: string;
  endpoint_count: number;
  schema_count: number;
  endpoints: Array<{
    method: string;
    path: string;
    summary: string;
    description: string;
    ai_explanation: string;
    tags: string[];
  }>;
  schemas: Record<string, {
    schema_name: string;
    schema_type: string;
    properties: Record<string, any>;
    required_fields: string[];
    description: string;
    ai_explanation: string;
    generated_sql: string;
  }>;
}

export default function DocumentAnalysisResults() {
  const params = useParams();
  const docId = params.id as string;

  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTab, setSelectedTab] = useState<'summary' | 'endpoints' | 'schemas'>('summary');
  const [copiedSql, setCopiedSql] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysis();
  }, [docId]);

  const fetchAnalysis = async () => {
    try {
      const res = await fetch(`/api/doc-analyzer/documents/${docId}/analysis`);

      if (!res.ok) {
        throw new Error('Failed to fetch analysis');
      }

      const data = await res.json();
      setAnalysis(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, schemaName: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSql(schemaName);
      setTimeout(() => setCopiedSql(null), 2000);
    } catch (err) {
      alert('Failed to copy to clipboard');
    }
  };

  const getMethodColor = (method: string) => {
    switch (method.toUpperCase()) {
      case 'GET': return 'bg-green-100 text-green-800';
      case 'POST': return 'bg-blue-100 text-blue-800';
      case 'PUT': return 'bg-yellow-100 text-yellow-800';
      case 'DELETE': return 'bg-red-100 text-red-800';
      case 'PATCH': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Failed to load analysis</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link href="/admin/doc-analyzer" className="text-blue-600 hover:text-blue-800">
            ← Back to Dashboard
          </Link>
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
              <h1 className="text-2xl font-bold text-gray-900">📋 Analysis Results</h1>
              <p className="text-sm text-gray-600">
                {analysis.endpoint_count} endpoints · {analysis.schema_count} schemas
              </p>
            </div>
            <Link
              href="/admin/doc-analyzer"
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setSelectedTab('summary')}
                className={`px-6 py-3 text-sm font-medium ${
                  selectedTab === 'summary'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📊 Summary
              </button>
              <button
                onClick={() => setSelectedTab('endpoints')}
                className={`px-6 py-3 text-sm font-medium ${
                  selectedTab === 'endpoints'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🔌 Endpoints ({analysis.endpoint_count})
              </button>
              <button
                onClick={() => setSelectedTab('schemas')}
                className={`px-6 py-3 text-sm font-medium ${
                  selectedTab === 'schemas'
                    ? 'border-b-2 border-blue-500 text-blue-600'
                    : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🗄️ Schemas ({analysis.schema_count})
              </button>
            </nav>
          </div>
        </div>

        {/* Summary Tab */}
        {selectedTab === 'summary' && (
          <div className="space-y-6">
            {/* AI Summary */}
            {analysis.summary && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">🤖 AI Summary</h2>
                <p className="text-gray-700 leading-relaxed">{analysis.summary}</p>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">API Endpoints</h3>
                <div className="text-4xl font-bold text-blue-600 mb-2">{analysis.endpoint_count}</div>
                <p className="text-sm text-gray-600">Total endpoints discovered</p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Schemas</h3>
                <div className="text-4xl font-bold text-purple-600 mb-2">{analysis.schema_count}</div>
                <p className="text-sm text-gray-600">Database tables ready to generate</p>
              </div>
            </div>
          </div>
        )}

        {/* Endpoints Tab */}
        {selectedTab === 'endpoints' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="divide-y divide-gray-200">
              {analysis.endpoints.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No endpoints found
                </div>
              ) : (
                analysis.endpoints.map((endpoint, idx) => (
                  <div key={idx} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded font-mono text-sm font-semibold ${getMethodColor(endpoint.method)}`}>
                          {endpoint.method}
                        </span>
                        <code className="text-sm font-mono text-gray-900">{endpoint.path}</code>
                      </div>
                      {endpoint.tags && endpoint.tags.length > 0 && (
                        <div className="flex gap-2">
                          {endpoint.tags.map((tag, i) => (
                            <span key={i} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {endpoint.summary && (
                      <div className="text-sm font-medium text-gray-900 mb-2">
                        {endpoint.summary}
                      </div>
                    )}

                    {endpoint.ai_explanation && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
                        <div className="flex items-start">
                          <span className="text-sm mr-2">💡</span>
                          <span className="text-sm text-blue-900">{endpoint.ai_explanation}</span>
                        </div>
                      </div>
                    )}

                    {endpoint.description && (
                      <div className="text-sm text-gray-600">
                        {endpoint.description}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Schemas Tab */}
        {selectedTab === 'schemas' && (
          <div className="space-y-6">
            {Object.keys(analysis.schemas).length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                No schemas found
              </div>
            ) : (
              Object.entries(analysis.schemas).map(([schemaName, schema]) => (
                <div key={schemaName} className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">🗄️ {schemaName}</h3>
                    {schema.description && (
                      <p className="text-sm text-gray-600 mt-1">{schema.description}</p>
                    )}
                  </div>

                  <div className="p-6">
                    {/* AI Explanation */}
                    {schema.ai_explanation && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                        <div className="flex items-start">
                          <span className="text-lg mr-2">🤖</span>
                          <div>
                            <div className="text-sm font-medium text-purple-900 mb-1">AI Explanation</div>
                            <div className="text-sm text-purple-800">{schema.ai_explanation}</div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Fields */}
                    <div className="mb-4">
                      <h4 className="text-sm font-semibold text-gray-900 mb-3">Fields ({Object.keys(schema.properties).length})</h4>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                        {Object.entries(schema.properties).map(([fieldName, fieldDef]: [string, any]) => (
                          <div key={fieldName} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <code className="text-sm font-mono text-blue-600">{fieldName}</code>
                              {schema.required_fields?.includes(fieldName) && (
                                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">required</span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500">
                              {fieldDef.type} {fieldDef.format && `(${fieldDef.format})`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Generated SQL */}
                    {schema.generated_sql && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-sm font-semibold text-gray-900">Generated SQL</h4>
                          <button
                            onClick={() => copyToClipboard(schema.generated_sql, schemaName)}
                            className="px-3 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 text-sm"
                          >
                            {copiedSql === schemaName ? '✓ Copied!' : '📋 Copy SQL'}
                          </button>
                        </div>
                        <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-xs">
                          {schema.generated_sql}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
