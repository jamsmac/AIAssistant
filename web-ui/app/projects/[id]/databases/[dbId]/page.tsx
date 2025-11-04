'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Plus, Edit2, Trash2, X, Loader2, Table } from 'lucide-react';
import { useApi } from '@/lib/useApi';
import { useToast } from '@/components/ui/Toast';

interface Database {
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

interface Record {
  id: number;
  database_id: number;
  data: { [key: string]: any };
  created_at: string;
  updated_at: string;
}

export default function DatabaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const dbId = params.dbId as string;
  const api = useApi();
  const { showToast } = useToast();

  const [database, setDatabase] = useState<Database | null>(null);
  const [records, setRecords] = useState<Record[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingRecord, setEditingRecord] = useState<Record | null>(null);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState<{ [key: string]: any }>({});

  useEffect(() => {
    fetchDatabaseDetails();
  }, [dbId]);

  const fetchDatabaseDetails = async () => {
    try {
      setLoading(true);

      const [dbData, recordsData] = await Promise.all([
        api.get<Database>(`/api/databases/${dbId}`),
        api.get<Record[]>(`/api/databases/${dbId}/records?limit=100`)
      ]);

      setDatabase(dbData);
      setRecords(recordsData);

      // Initialize form data with default values
      const initialData: { [key: string]: any } = {};
      dbData.schema.columns.forEach(col => {
        initialData[col.name] = col.default_value || '';
      });
      setFormData(initialData);
    } catch (error) {
      console.error('Error fetching database details:', error);
    } finally {
      setLoading(false);
    }
  };

  const createRecord = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!database) return;

    // Validate required fields
    const missingFields = database.schema.columns
      .filter(col => col.required && !formData[col.name])
      .map(col => col.name);

    if (missingFields.length > 0) {
      showToast(`Missing required fields: ${missingFields.join(', ')}`, 'error');
      return;
    }

    try {
      setCreating(true);

      await api.post(`/api/databases/${dbId}/records`, {
        data: formData
      });

      showToast('Record created successfully!', 'success');
      setShowCreateModal(false);

      // Reset form
      const initialData: { [key: string]: any } = {};
      database.schema.columns.forEach(col => {
        initialData[col.name] = col.default_value || '';
      });
      setFormData(initialData);

      await fetchDatabaseDetails();
    } catch (error) {
      console.error('Error creating record:', error);
    } finally {
      setCreating(false);
    }
  };

  const updateRecord = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!editingRecord || !database) return;

    // Validate required fields
    const missingFields = database.schema.columns
      .filter(col => col.required && !formData[col.name])
      .map(col => col.name);

    if (missingFields.length > 0) {
      showToast(`Missing required fields: ${missingFields.join(', ')}`, 'error');
      return;
    }

    try {
      setCreating(true);

      await api.put(`/api/databases/${dbId}/records/${editingRecord.id}`, {
        data: formData
      });

      showToast('Record updated successfully!', 'success');
      setShowEditModal(false);
      setEditingRecord(null);
      await fetchDatabaseDetails();
    } catch (error) {
      console.error('Error updating record:', error);
    } finally {
      setCreating(false);
    }
  };

  const deleteRecord = async (recordId: number) => {
    if (!confirm('Are you sure you want to delete this record?')) return;

    try {
      await api.delete(`/api/databases/${dbId}/records/${recordId}`);
      showToast('Record deleted successfully!', 'success');
      await fetchDatabaseDetails();
    } catch (error) {
      console.error('Error deleting record:', error);
    }
  };

  const openEditModal = (record: Record) => {
    setEditingRecord(record);
    setFormData(record.data);
    setShowEditModal(true);
  };

  const openCreateModal = () => {
    if (!database) return;

    // Reset form with default values
    const initialData: { [key: string]: any } = {};
    database.schema.columns.forEach(col => {
      initialData[col.name] = col.default_value || '';
    });
    setFormData(initialData);
    setShowCreateModal(true);
  };

  const renderFormField = (column: Column) => {
    const value = formData[column.name] || '';

    switch (column.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setFormData({ ...formData, [column.name]: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={column.required}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => setFormData({ ...formData, [column.name]: parseFloat(e.target.value) || 0 })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={column.required}
          />
        );

      case 'boolean':
        return (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={!!value}
              onChange={(e) => setFormData({ ...formData, [column.name]: e.target.checked })}
              className="rounded"
            />
            <span className="text-gray-300">{value ? 'Yes' : 'No'}</span>
          </label>
        );

      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => setFormData({ ...formData, [column.name]: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={column.required}
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => setFormData({ ...formData, [column.name]: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            required={column.required}
          >
            <option value="">Select...</option>
            {column.options?.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-800 rounded w-1/4 mb-8"></div>
            <div className="h-64 bg-gray-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!database) {
    return (
      <div className="min-h-screen bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Database not found</h1>
          <button
            onClick={() => router.push(`/projects/${projectId}`)}
            className="text-blue-400 hover:text-blue-300"
          >
            Back to Project
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
          onClick={() => router.push(`/projects/${projectId}`)}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Project
        </button>

        {/* Database Info */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{database.name}</h1>
              <p className="text-gray-400">
                {records.length} {records.length === 1 ? 'record' : 'records'} · {database.schema.columns.length} columns
              </p>
            </div>
          </div>

          {/* Schema Info */}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-2">Schema:</h3>
            <div className="flex flex-wrap gap-2">
              {database.schema.columns.map((col) => (
                <div
                  key={col.name}
                  className="px-3 py-1 bg-gray-700 rounded-lg text-sm"
                >
                  <span className="text-white font-medium">{col.name}</span>
                  <span className="text-gray-400 ml-2">({col.type})</span>
                  {col.required && <span className="text-red-400 ml-1">*</span>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Records Section */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Records</h2>
          <button
            onClick={openCreateModal}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
          >
            <Plus className="w-5 h-5" />
            New Record
          </button>
        </div>

        {/* Empty State */}
        {records.length === 0 && (
          <div className="text-center py-20 bg-gray-800 rounded-xl border border-gray-700">
            <Table className="w-20 h-20 text-gray-600 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold text-gray-400 mb-2">No records yet</h3>
            <p className="text-gray-500 mb-6">Add your first record to this database</p>
            <button
              onClick={openCreateModal}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
            >
              <Plus className="w-5 h-5" />
              Add Record
            </button>
          </div>
        )}

        {/* Records Table */}
        {records.length > 0 && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    {database.schema.columns.map((col) => (
                      <th key={col.name} className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        {col.name}
                      </th>
                    ))}
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {records.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-750 transition-colors">
                      {database.schema.columns.map((col) => (
                        <td key={col.name} className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                          {col.type === 'boolean'
                            ? (record.data[col.name] ? '✓' : '✗')
                            : record.data[col.name]?.toString() || '-'}
                        </td>
                      ))}
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                        <button
                          onClick={() => openEditModal(record)}
                          className="text-blue-400 hover:text-blue-300 mr-3"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deleteRecord(record.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Record Modal */}
      {(showCreateModal || showEditModal) && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => {
            if (!creating) {
              setShowCreateModal(false);
              setShowEditModal(false);
              setEditingRecord(null);
            }
          }}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full border border-gray-700 shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                {showEditModal ? 'Edit Record' : 'Create New Record'}
              </h2>
              <button
                onClick={() => {
                  if (!creating) {
                    setShowCreateModal(false);
                    setShowEditModal(false);
                    setEditingRecord(null);
                  }
                }}
                disabled={creating}
                className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={showEditModal ? updateRecord : createRecord}>
              <div className="space-y-4 mb-6">
                {database.schema.columns.map((column) => (
                  <div key={column.name}>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      {column.name}
                      {column.required && <span className="text-red-400 ml-1">*</span>}
                      <span className="text-gray-500 ml-2">({column.type})</span>
                    </label>
                    {renderFormField(column)}
                  </div>
                ))}
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setShowEditModal(false);
                    setEditingRecord(null);
                  }}
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      {showEditModal ? 'Updating...' : 'Creating...'}
                    </>
                  ) : (
                    showEditModal ? 'Update Record' : 'Create Record'
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
