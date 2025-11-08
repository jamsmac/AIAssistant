'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function NewDocumentAnalyzer() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    type: 'openapi',
    source_url: '',
    analyze_immediately: true
  });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setUploading(true);

    try {
      const res = await fetch('/api/doc-analyzer/documents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to create document');
      }

      const data = await res.json();

      // Redirect based on whether analysis was started
      if (formData.analyze_immediately) {
        alert('✅ Document submitted! Analysis has started. Redirecting to dashboard...');
        router.push('/admin/doc-analyzer');
      } else {
        alert('✅ Document created successfully! You can trigger analysis from the dashboard.');
        router.push('/admin/doc-analyzer');
      }

    } catch (err: any) {
      setError(err.message || 'Failed to submit document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">📚 Analyze Documentation</h1>
              <p className="text-sm text-gray-600">Submit API documentation for AI-powered analysis</p>
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

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Info Card */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <div className="text-2xl mr-3">ℹ️</div>
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">What happens during analysis?</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• AI reads and understands the API documentation</li>
                <li>• Endpoints are extracted and explained in simple terms</li>
                <li>• Data schemas are identified and SQL tables are auto-generated</li>
                <li>• Visual diagrams show the API structure</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">❌</span>
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {/* Document Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="My API Documentation"
              required
            />
            <p className="text-xs text-gray-500 mt-1">A friendly name to identify this documentation</p>
          </div>

          {/* Document Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Documentation Type *
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="openapi">📋 OpenAPI 3.x / Swagger</option>
              <option value="pdf" disabled>📄 PDF Documentation (Coming Soon)</option>
              <option value="google_sheets" disabled>📊 Google Sheets (Coming Soon)</option>
            </select>
          </div>

          {/* Source URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Documentation URL *
            </label>
            <input
              type="url"
              value={formData.source_url}
              onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://api.example.com/openapi.json"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              URL to the OpenAPI/Swagger JSON or YAML file
            </p>
          </div>

          {/* Example URLs */}
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Example URLs to try:</p>
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setFormData({
                  ...formData,
                  name: 'Petstore API Example',
                  source_url: 'https://petstore.swagger.io/v2/swagger.json'
                })}
                className="block text-sm text-blue-600 hover:text-blue-800"
              >
                📋 https://petstore.swagger.io/v2/swagger.json
              </button>
              <button
                type="button"
                onClick={() => setFormData({
                  ...formData,
                  name: 'GitHub API',
                  source_url: 'https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json'
                })}
                className="block text-sm text-blue-600 hover:text-blue-800"
              >
                📋 GitHub API (OpenAPI)
              </button>
            </div>
          </div>

          {/* Analysis Options */}
          <div className="border-t pt-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="analyze_immediately"
                checked={formData.analyze_immediately}
                onChange={(e) => setFormData({ ...formData, analyze_immediately: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="analyze_immediately" className="ml-2 block text-sm text-gray-700">
                Start analysis immediately
              </label>
            </div>
            <p className="text-xs text-gray-500 mt-1 ml-6">
              If unchecked, you can manually trigger analysis later from the dashboard
            </p>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => router.push('/admin/doc-analyzer')}
              className="flex-1 px-4 py-3 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Submitting...
                </span>
              ) : (
                '🔍 Analyze Documentation'
              )}
            </button>
          </div>
        </form>

        {/* Help Section */}
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-3">💡 Tips for best results:</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start">
              <span className="mr-2">✓</span>
              <span>Use publicly accessible URLs (no authentication required)</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">✓</span>
              <span>OpenAPI 3.x or Swagger 2.0 formats work best</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">✓</span>
              <span>Files can be in JSON or YAML format</span>
            </li>
            <li className="flex items-start">
              <span className="mr-2">✓</span>
              <span>Analysis typically takes 30-60 seconds depending on API size</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
