'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus, Play, Edit2, Trash2, ChevronDown, ChevronUp,
  Clock, Zap, Webhook, Mail, Database as DatabaseIcon,
  X, Loader2, Search, Filter, Check, AlertCircle, CheckCircle2
} from 'lucide-react';
import { useApi } from '@/lib/useApi';
import { useToast } from '@/components/ui/Toast';

// Types
interface WorkflowTrigger {
  type: 'manual' | 'schedule' | 'webhook' | 'email_received' | 'record_created';
  config: Record<string, any>;
}

interface WorkflowAction {
  type: string;
  config: Record<string, any>;
}

interface Workflow {
  id: number;
  user_id: number;
  name: string;
  trigger: WorkflowTrigger;
  actions: WorkflowAction[];
  enabled: boolean;
  created_at: string;
  last_execution?: string;
}

interface Execution {
  id: number;
  workflow_id: number;
  status: string;
  result: any;
  error: string | null;
  executed_at: string;
}

const TRIGGER_TYPES = [
  { value: 'manual', label: 'Manual', icon: Play, color: 'blue' },
  { value: 'schedule', label: 'Schedule', icon: Clock, color: 'purple' },
  { value: 'webhook', label: 'Webhook', icon: Webhook, color: 'green' },
  { value: 'email_received', label: 'Email Received', icon: Mail, color: 'orange' },
  { value: 'record_created', label: 'Record Created', icon: DatabaseIcon, color: 'pink' },
];

const ACTION_TYPES = [
  { value: 'send_email', label: 'Send Email', fields: ['to', 'subject', 'body'] },
  { value: 'create_record', label: 'Create Record', fields: ['database_id', 'data'] },
  { value: 'update_record', label: 'Update Record', fields: ['record_id', 'database_id', 'data'] },
  { value: 'delete_record', label: 'Delete Record', fields: ['record_id', 'database_id'] },
  { value: 'call_webhook', label: 'Call Webhook', fields: ['url', 'payload'] },
  { value: 'run_ai_agent', label: 'Run AI Agent', fields: ['prompt', 'task_type'] },
  { value: 'send_notification', label: 'Send Notification', fields: ['message', 'level'] },
  { value: 'send_telegram', label: 'Send Telegram', fields: ['chat_id', 'message'] },
  { value: 'create_project', label: 'Create Project', fields: ['name', 'description'] },
  { value: 'execute_workflow', label: 'Execute Workflow', fields: ['workflow_id', 'context'] },
];

export default function WorkflowsPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showNewModal, setShowNewModal] = useState(false);
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [showResultModal, setShowResultModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // State
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionDetails, setExecutionDetails] = useState<Execution | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [executions, setExecutions] = useState<Record<number, Execution[]>>({});
  const [executing, setExecuting] = useState<number | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'enabled' | 'disabled'>('all');

  // New workflow form
  const [formName, setFormName] = useState('');
  const [formTrigger, setFormTrigger] = useState<WorkflowTrigger>({
    type: 'manual',
    config: {}
  });
  const [formActions, setFormActions] = useState<WorkflowAction[]>([
    { type: 'send_notification', config: {} }
  ]);
  const [formEnabled, setFormEnabled] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(`${API_URL}/api/workflows`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        router.push('/login');
        return;
      }

      if (!response.ok) throw new Error('Failed to fetch workflows');

      const data = await response.json();
      setWorkflows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutions = async (workflowId: number) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(
        `${API_URL}/api/workflows/${workflowId}/executions?limit=10`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );

      if (!response.ok) throw new Error('Failed to fetch executions');

      const data = await response.json();
      setExecutions(prev => ({ ...prev, [workflowId]: data }));
    } catch (err) {
      console.error('Error fetching executions:', err);
    }
  };

  const toggleExpand = async (workflowId: number) => {
    if (expandedRow === workflowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(workflowId);
      if (!executions[workflowId]) {
        await fetchExecutions(workflowId);
      }
    }
  };

  const executeWorkflow = async (workflow: Workflow) => {
    try {
      setExecuting(workflow.id);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(
        `${API_URL}/api/workflows/${workflow.id}/execute`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute workflow');
      }

      const result = await response.json();
      setExecutionResult(result);
      setShowExecuteModal(false);
      setShowResultModal(true);

      // Refresh executions if row is expanded
      if (expandedRow === workflow.id) {
        await fetchExecutions(workflow.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setExecuting(null);
    }
  };

  const toggleWorkflowStatus = async (workflow: Workflow) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(
        `${API_URL}/api/workflows/${workflow.id}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ enabled: !workflow.enabled }),
        }
      );

      if (!response.ok) throw new Error('Failed to update workflow');

      await fetchWorkflows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update status');
    }
  };

  const deleteWorkflow = async (workflowId: number) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(
        `${API_URL}/api/workflows/${workflowId}`,
        {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (!response.ok) throw new Error('Failed to delete workflow');

      await fetchWorkflows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete workflow');
    }
  };

  const createWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) return;

    try {
      setCreating(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_URL}/api/workflows`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formName.trim(),
          trigger: formTrigger,
          actions: formActions,
          enabled: formEnabled,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create workflow');
      }

      setShowNewModal(false);
      resetForm();
      await fetchWorkflows();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow');
    } finally {
      setCreating(false);
    }
  };

  const resetForm = () => {
    setFormName('');
    setFormTrigger({ type: 'manual', config: {} });
    setFormActions([{ type: 'send_notification', config: {} }]);
    setFormEnabled(true);
  };

  const addAction = () => {
    setFormActions([...formActions, { type: 'send_notification', config: {} }]);
  };

  const removeAction = (index: number) => {
    setFormActions(formActions.filter((_, i) => i !== index));
  };

  const updateAction = (index: number, field: 'type' | 'config', value: any) => {
    const newActions = [...formActions];
    if (field === 'type') {
      newActions[index] = { type: value, config: {} };
    } else {
      newActions[index].config = value;
    }
    setFormActions(newActions);
  };

  const moveAction = (index: number, direction: 'up' | 'down') => {
    if (direction === 'up' && index === 0) return;
    if (direction === 'down' && index === formActions.length - 1) return;

    const newActions = [...formActions];
    const swapIndex = direction === 'up' ? index - 1 : index + 1;
    [newActions[index], newActions[swapIndex]] = [newActions[swapIndex], newActions[index]];
    setFormActions(newActions);
  };

  const getTriggerBadge = (trigger: WorkflowTrigger) => {
    const triggerType = TRIGGER_TYPES.find(t => t.value === trigger.type);
    if (!triggerType) return null;

    const Icon = triggerType.icon;
    const colorClasses = {
      blue: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
      green: 'bg-green-500/10 text-green-400 border-green-500/30',
      orange: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      pink: 'bg-pink-500/10 text-pink-400 border-pink-500/30',
    };

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md border text-xs font-medium ${colorClasses[triggerType.color as keyof typeof colorClasses]}`}>
        <Icon className="w-3 h-3" />
        {triggerType.label}
      </span>
    );
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const filteredWorkflows = workflows.filter(w => {
    const matchesSearch = w.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' ||
      (filterStatus === 'enabled' && w.enabled) ||
      (filterStatus === 'disabled' && !w.enabled);
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-white">Workflows</h1>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>

        {/* Error Toast */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500 rounded-xl text-red-400 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-center gap-2 bg-gray-800 border border-gray-700 rounded-lg p-1">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                filterStatus === 'all' ? 'bg-blue-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterStatus('enabled')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                filterStatus === 'enabled' ? 'bg-green-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Enabled
            </button>
            <button
              onClick={() => setFilterStatus('disabled')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                filterStatus === 'disabled' ? 'bg-gray-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Disabled
            </button>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="text-center py-20">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading workflows...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && filteredWorkflows.length === 0 && (
          <div className="text-center py-20 bg-gray-800 rounded-xl border border-gray-700">
            <Zap className="w-20 h-20 text-gray-600 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-400 mb-2">
              {searchQuery || filterStatus !== 'all' ? 'No workflows found' : 'No workflows yet'}
            </h2>
            <p className="text-gray-500 mb-6">
              {searchQuery || filterStatus !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first workflow to automate tasks!'}
            </p>
            {!searchQuery && filterStatus === 'all' && (
              <button
                onClick={() => setShowNewModal(true)}
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105"
              >
                <Plus className="w-5 h-5" />
                Create Workflow
              </button>
            )}
          </div>
        )}

        {/* Workflows Table */}
        {!loading && filteredWorkflows.length > 0 && (
          <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-900/50 border-b border-gray-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Trigger
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    History
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredWorkflows.map((workflow) => (
                  <>
                    <tr key={workflow.id} className="hover:bg-gray-700/50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="text-white font-medium">{workflow.name}</span>
                          <span className="text-xs text-gray-400">{workflow.actions.length} actions</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getTriggerBadge(workflow.trigger)}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => toggleWorkflowStatus(workflow)}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                            workflow.enabled
                              ? 'bg-green-500/10 text-green-400 border border-green-500/30 hover:bg-green-500/20'
                              : 'bg-gray-700 text-gray-400 border border-gray-600 hover:bg-gray-600'
                          }`}
                        >
                          {workflow.enabled ? <Check className="w-4 h-4" /> : null}
                          {workflow.enabled ? 'Enabled' : 'Disabled'}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setSelectedWorkflow(workflow);
                              setShowExecuteModal(true);
                            }}
                            disabled={!workflow.enabled || executing === workflow.id}
                            className="p-2 bg-blue-500/10 text-blue-400 rounded-lg hover:bg-blue-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Execute"
                          >
                            {executing === workflow.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </button>
                          <button
                            onClick={() => router.push(`/workflows/${workflow.id}/edit`)}
                            className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteWorkflow(workflow.id)}
                            className="p-2 bg-red-500/10 text-red-400 rounded-lg hover:bg-red-500/20 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <button
                          onClick={() => toggleExpand(workflow.id)}
                          className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          {expandedRow === workflow.id ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Executions */}
                    {expandedRow === workflow.id && (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 bg-gray-900/50">
                          <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-gray-400 mb-3">Recent Executions</h3>
                            {!executions[workflow.id] ? (
                              <div className="text-center py-4">
                                <Loader2 className="w-6 h-6 text-blue-500 animate-spin mx-auto" />
                              </div>
                            ) : executions[workflow.id].length === 0 ? (
                              <div className="text-center py-4 text-gray-500">
                                No executions yet
                              </div>
                            ) : (
                              <div className="space-y-2">
                                {executions[workflow.id].map((exec) => (
                                  <div
                                    key={exec.id}
                                    className="flex items-center justify-between p-3 bg-gray-800 rounded-lg border border-gray-700"
                                  >
                                    <div className="flex items-center gap-4">
                                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                                        exec.status === 'completed'
                                          ? 'bg-green-500/10 text-green-400'
                                          : 'bg-red-500/10 text-red-400'
                                      }`}>
                                        {exec.status === 'completed' ? (
                                          <CheckCircle2 className="w-3 h-3" />
                                        ) : (
                                          <AlertCircle className="w-3 h-3" />
                                        )}
                                        {exec.status}
                                      </span>
                                      <span className="text-sm text-gray-400">
                                        {getRelativeTime(exec.executed_at)}
                                      </span>
                                    </div>
                                    <button
                                      onClick={() => {
                                        setExecutionDetails(exec);
                                        setShowDetailsModal(true);
                                      }}
                                      className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                    >
                                      View Details
                                    </button>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* New Workflow Modal */}
      {showNewModal && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto"
          onClick={() => !creating && setShowNewModal(false)}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-3xl w-full border border-gray-700 shadow-2xl my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Create New Workflow</h2>
              <button
                onClick={() => !creating && setShowNewModal(false)}
                disabled={creating}
                className="text-gray-400 hover:text-white transition-colors disabled:opacity-50"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={createWorkflow} className="space-y-6">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Workflow Name *
                </label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="My Automation Workflow"
                  disabled={creating}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  required
                />
              </div>

              {/* Trigger */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trigger Type *
                </label>
                <select
                  value={formTrigger.type}
                  onChange={(e) => setFormTrigger({
                    type: e.target.value as any,
                    config: {}
                  })}
                  disabled={creating}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {TRIGGER_TYPES.map((trigger) => (
                    <option key={trigger.value} value={trigger.value}>
                      {trigger.label}
                    </option>
                  ))}
                </select>

                {/* Trigger Config */}
                {formTrigger.type === 'schedule' && (
                  <div className="mt-3">
                    <label className="block text-xs text-gray-400 mb-1">Cron Expression</label>
                    <input
                      type="text"
                      value={formTrigger.config.cron || ''}
                      onChange={(e) => setFormTrigger({
                        ...formTrigger,
                        config: { ...formTrigger.config, cron: e.target.value }
                      })}
                      placeholder="0 0 * * *"
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}

                {formTrigger.type === 'webhook' && (
                  <div className="mt-3 p-3 bg-gray-900 rounded-lg border border-gray-700">
                    <p className="text-xs text-gray-400">Webhook URL will be generated after creation</p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-300">
                    Actions * ({formActions.length})
                  </label>
                  <button
                    type="button"
                    onClick={addAction}
                    disabled={creating}
                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50"
                  >
                    + Add Action
                  </button>
                </div>

                <div className="space-y-3">
                  {formActions.map((action, index) => (
                    <div key={index} className="p-4 bg-gray-900 rounded-lg border border-gray-700">
                      <div className="flex items-start justify-between mb-3">
                        <span className="text-xs font-medium text-gray-400">Action {index + 1}</span>
                        <div className="flex items-center gap-1">
                          {index > 0 && (
                            <button
                              type="button"
                              onClick={() => moveAction(index, 'up')}
                              className="p-1 text-gray-400 hover:text-white transition-colors"
                              title="Move up"
                            >
                              <ChevronUp className="w-4 h-4" />
                            </button>
                          )}
                          {index < formActions.length - 1 && (
                            <button
                              type="button"
                              onClick={() => moveAction(index, 'down')}
                              className="p-1 text-gray-400 hover:text-white transition-colors"
                              title="Move down"
                            >
                              <ChevronDown className="w-4 h-4" />
                            </button>
                          )}
                          {formActions.length > 1 && (
                            <button
                              type="button"
                              onClick={() => removeAction(index)}
                              className="p-1 text-red-400 hover:text-red-300 transition-colors"
                              title="Remove"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>

                      <select
                        value={action.type}
                        onChange={(e) => updateAction(index, 'type', e.target.value)}
                        disabled={creating}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 mb-3"
                      >
                        {ACTION_TYPES.map((actionType) => (
                          <option key={actionType.value} value={actionType.value}>
                            {actionType.label}
                          </option>
                        ))}
                      </select>

                      {/* Action Config Fields */}
                      <div className="space-y-2">
                        {action.type === 'send_notification' && (
                          <>
                            <input
                              type="text"
                              value={action.config.message || ''}
                              onChange={(e) => updateAction(index, 'config', {
                                ...action.config,
                                message: e.target.value
                              })}
                              placeholder="Message"
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <select
                              value={action.config.level || 'info'}
                              onChange={(e) => updateAction(index, 'config', {
                                ...action.config,
                                level: e.target.value
                              })}
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value="info">Info</option>
                              <option value="warning">Warning</option>
                              <option value="error">Error</option>
                            </select>
                          </>
                        )}

                        {action.type === 'call_webhook' && (
                          <>
                            <input
                              type="url"
                              value={action.config.url || ''}
                              onChange={(e) => updateAction(index, 'config', {
                                ...action.config,
                                url: e.target.value
                              })}
                              placeholder="https://api.example.com/webhook"
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <textarea
                              value={action.config.payload ? JSON.stringify(action.config.payload, null, 2) : '{}'}
                              onChange={(e) => {
                                try {
                                  const payload = JSON.parse(e.target.value);
                                  updateAction(index, 'config', {
                                    ...action.config,
                                    payload
                                  });
                                } catch (err) {
                                  // Invalid JSON, keep typing
                                }
                              }}
                              placeholder='{"key": "value"}'
                              rows={3}
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                            />
                          </>
                        )}

                        {action.type === 'create_record' && (
                          <>
                            <input
                              type="number"
                              value={action.config.database_id || ''}
                              onChange={(e) => updateAction(index, 'config', {
                                ...action.config,
                                database_id: parseInt(e.target.value)
                              })}
                              placeholder="Database ID"
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                            <textarea
                              value={action.config.data ? JSON.stringify(action.config.data, null, 2) : '{}'}
                              onChange={(e) => {
                                try {
                                  const data = JSON.parse(e.target.value);
                                  updateAction(index, 'config', {
                                    ...action.config,
                                    data
                                  });
                                } catch (err) {
                                  // Invalid JSON
                                }
                              }}
                              placeholder='{"field": "value"}'
                              rows={3}
                              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                            />
                          </>
                        )}

                        {/* Other action types - simplified config */}
                        {!['send_notification', 'call_webhook', 'create_record'].includes(action.type) && (
                          <textarea
                            value={JSON.stringify(action.config, null, 2)}
                            onChange={(e) => {
                              try {
                                const config = JSON.parse(e.target.value);
                                updateAction(index, 'config', config);
                              } catch (err) {
                                // Invalid JSON
                              }
                            }}
                            placeholder='{"field": "value"}'
                            rows={3}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Enabled */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formEnabled}
                  onChange={(e) => setFormEnabled(e.target.checked)}
                  disabled={creating}
                  className="w-4 h-4 rounded border-gray-700 bg-gray-900 text-blue-500 focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                />
                <label htmlFor="enabled" className="text-sm text-gray-300">
                  Enable workflow immediately
                </label>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-700">
                <button
                  type="button"
                  onClick={() => {
                    setShowNewModal(false);
                    resetForm();
                  }}
                  disabled={creating}
                  className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!formName.trim() || formActions.length === 0 || creating}
                  className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Workflow'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Execute Confirmation Modal */}
      {showExecuteModal && selectedWorkflow && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
          onClick={() => setShowExecuteModal(false)}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-gray-700 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-bold text-white mb-4">Execute Workflow</h3>
            <p className="text-gray-300 mb-6">
              Are you sure you want to execute <span className="font-semibold text-blue-400">{selectedWorkflow.name}</span>?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowExecuteModal(false)}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => executeWorkflow(selectedWorkflow)}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Execute
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Result Modal */}
      {showResultModal && executionResult && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto"
          onClick={() => setShowResultModal(false)}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full border border-gray-700 shadow-2xl my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">Execution Result</h3>
              <button
                onClick={() => setShowResultModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Status */}
              <div className="flex items-center gap-3 p-4 bg-gray-900 rounded-lg border border-gray-700">
                {executionResult.status === 'completed' ? (
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-400" />
                )}
                <div>
                  <div className="text-sm font-medium text-gray-400">Status</div>
                  <div className={`text-lg font-semibold ${
                    executionResult.status === 'completed' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {executionResult.status}
                  </div>
                </div>
              </div>

              {/* Execution Time */}
              <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
                <div className="text-sm font-medium text-gray-400 mb-1">Executed At</div>
                <div className="text-white">{new Date(executionResult.executed_at).toLocaleString()}</div>
              </div>

              {/* Results */}
              {executionResult.result && (
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
                  <div className="text-sm font-medium text-gray-400 mb-2">Results</div>
                  <pre className="text-xs text-gray-300 overflow-x-auto bg-gray-800 p-3 rounded-lg border border-gray-700">
                    {JSON.stringify(executionResult.result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error */}
              {executionResult.error && (
                <div className="p-4 bg-red-500/10 rounded-lg border border-red-500">
                  <div className="text-sm font-medium text-red-400 mb-1">Error</div>
                  <div className="text-red-300">{executionResult.error}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Execution Details Modal */}
      {showDetailsModal && executionDetails && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto"
          onClick={() => setShowDetailsModal(false)}
        >
          <div
            className="bg-gray-800 rounded-xl p-6 max-w-2xl w-full border border-gray-700 shadow-2xl my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white">Execution Details</h3>
              <button
                onClick={() => setShowDetailsModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Status */}
              <div className="flex items-center gap-3 p-4 bg-gray-900 rounded-lg border border-gray-700">
                {executionDetails.status === 'completed' ? (
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-red-400" />
                )}
                <div>
                  <div className="text-sm font-medium text-gray-400">Status</div>
                  <div className={`text-lg font-semibold ${
                    executionDetails.status === 'completed' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {executionDetails.status}
                  </div>
                </div>
              </div>

              {/* Execution Time */}
              <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
                <div className="text-sm font-medium text-gray-400 mb-1">Executed At</div>
                <div className="text-white">{new Date(executionDetails.executed_at).toLocaleString()}</div>
              </div>

              {/* Results */}
              {executionDetails.result && (
                <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
                  <div className="text-sm font-medium text-gray-400 mb-2">Full Log</div>
                  <pre className="text-xs text-gray-300 overflow-x-auto bg-gray-800 p-3 rounded-lg border border-gray-700 max-h-96">
                    {JSON.stringify(executionDetails.result, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error */}
              {executionDetails.error && (
                <div className="p-4 bg-red-500/10 rounded-lg border border-red-500">
                  <div className="text-sm font-medium text-red-400 mb-1">Error</div>
                  <div className="text-red-300">{executionDetails.error}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
