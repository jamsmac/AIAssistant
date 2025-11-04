'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Database, Plus, Calendar, Edit2, Trash2, X, Loader2 } from 'lucide-react';
import { API_URL } from '@/lib/config';
import { useApi } from '@/lib/useApi';
import { useToast } from '@/components/ui/Toast';

interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  database_count: number;
}

interface DatabaseItem {
  id: number;
  project_id: number;
  name: string;
  schema: {
    columns: Column[];
  };
  record_count: number;
  created_at: string;
}

interface Column {
  name: string;
  type: 'text' | 'number' | 'boolean' | 'date' | 'select';
  required: boolean;
  default_value?: any;
  options?: string[];
}

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const api = useApi();
  const { showToast } = useToast();

  const [project, setProject] = useState<Project | null>(null);
  const [databases, setDatabases] = useState<DatabaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);

  // Form state
  const [dbName, setDbName] = useState('');
  const [columns, setColumns] = useState<Column[]>([
    { name: 'name', type: 'text', required: true }
  ]);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      setLoading(true);

      const [projectData, databasesData] = await Promise.all([
        api.get<Project>(`/api/projects/${projectId}`),
        api.get<DatabaseItem[]>(`/api/databases?project_id=${projectId}`)
      ]);

      setProject(projectData);
      setDatabases(databasesData);
    } catch (error) {
      console.error('Error fetching project details:', error);
    } finally {
      setLoading(false);
    }
  };

  const createDatabase = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!dbName.trim() || columns.length === 0) {
      showToast('Please provide database name and at least one column', 'error');
      return;
    }

    try {
      setCreating(true);

      await api.post('/api/databases', {
        project_id: parseInt(projectId),
        name: dbName.trim(),
        schema: { columns }
      });

      showToast('Database created successfully!', 'success');
      setShowCreateModal(false);
      setDbName('');
      setColumns([{ name: 'name', type: 'text', required: true }]);
      await fetchProjectDetails();
    } catch (error) {
      console.error('Error creating database:', error);
    } finally {
      setCreating(false);
    }
  };

  const addColumn = () => {
    setColumns([...columns, { name: '', type: 'text', required: false }]);
  };

  const removeColumn = (index: number) => {
    setColumns(columns.filter((_, i) => i !== index));
  };

  const updateColumn = (index: number, field: keyof Column, value: any) => {
    const newColumns = [...columns];
    newColumns[index] = { ...newColumns[index], [field]: value };
    setColumns(newColumns);
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    return `${Math.floor(diffDays / 365)} years ago`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-800 rounded w-1/4 mb-8"></div>
            <div className="h-32 bg-gray-800 rounded mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-40 bg-gray-800 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Project not found</h1>
          <button
            onClick={() => router.push('/projects')}
            className="text-blue-400 hover:text-blue-300"
          >
            Back to Projects
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <button
          onClick={() => router.push('/projects')}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Projects
        </button>

        {/* Project Info */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{project.name}</h1>
              {project.description && (
                <p className="text-gray-400">{project.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              <span>{databases.length} {databases.length === 1 ? 'database' : 'databases'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>Created {getRelativeTime(project.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Databases Section */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Databases</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
          >
            <Plus className="w-5 h-5" />
            New Database
          </button>
        </div>

        {/* Empty State */}
        {databases.length === 0 && (
          <div className="text-center py-20 bg-gray-800 rounded-xl border border-gray-700">
            <Database className="w-20 h-20 text-gray-600 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-gray-400 mb-2">No databases yet</h3>
            <p className="text-gray-500 mb-6">Create your first database to start storing data</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
            >
              <Plus className="w-5 h-5" />
              Create Database
            </button>
          </div>
        )}

        {/* Databases Grid */}
        {databases.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {databases.map((db) => (
              <div
                key={db.id}
                onClick={() => router.push(`/projects/${projectId}/databases/${db.id}`)}
                className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 hover:shadow-2xl transition-all duration-200 cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors">
                    {db.name}
                  </h3>
                </div>

                <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                  <div>
                    <span className="text-gray-400 font-semibold">{db.record_count}</span> records
                  </div>
                  <div>
                    <span className="text-gray-400 font-semibold">{db.schema.columns.length}</span> columns
                  </div>
                </div>

                <div className="text-xs text-gray-600">
                  Created {getRelativeTime(db.created_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Database Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => !creating && setShowCreateModal(false)}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full border border-gray-700 shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Create New Database</h2>
              <button
                onClick={() => !creating && setShowCreateModal(false)}
                disabled={creating}
                className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={createDatabase}>
              <div className="mb-6">
                <label htmlFor="dbName" className="block text-sm font-medium text-gray-300 mb-2">
                  Database Name *
                </label>
                <input
                  type="text"
                  id="dbName"
                  value={dbName}
                  onChange={(e) => setDbName(e.target.value)}
                  placeholder="customers"
                  disabled={creating}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  required
                />
              </div>

              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <label className="text-sm font-medium text-gray-300">
                    Columns *
                  </label>
                  <button
                    type="button"
                    onClick={addColumn}
                    disabled={creating}
                    className="text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50"
                  >
                    + Add Column
                  </button>
                </div>

                <div className="space-y-3">
                  {columns.map((column, index) => (
                    <div key={index} className="flex gap-2 items-start">
                      <input
                        type="text"
                        value={column.name}
                        onChange={(e) => updateColumn(index, 'name', e.target.value)}
                        placeholder="Column name"
                        disabled={creating}
                        className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm disabled:opacity-50"
                        required
                      />
                      <select
                        value={column.type}
                        onChange={(e) => updateColumn(index, 'type', e.target.value)}
                        disabled={creating}
                        className="px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm disabled:opacity-50"
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                        <option value="date">Date</option>
                        <option value="select">Select</option>
                      </select>
                      <label className="flex items-center gap-2 px-3 py-2 text-sm text-gray-300">
                        <input
                          type="checkbox"
                          checked={column.required}
                          onChange={(e) => updateColumn(index, 'required', e.target.checked)}
                          disabled={creating}
                          className="rounded"
                        />
                        Required
                      </label>
                      {columns.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeColumn(index)}
                          disabled={creating}
                          className="p-2 text-red-400 hover:text-red-300 disabled:opacity-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!dbName.trim() || columns.length === 0 || creating}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Database'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
