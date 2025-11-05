'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import type { WorkflowResult } from '@/types/workflows';
import { Plus, Search, Filter, Loader2 } from 'lucide-react';
import { useApi } from '@/lib/useApi';
import { useToast } from '@/components/ui/Toast';
import { API_URL } from '@/lib/config';

// Lazy load components
const WorkflowCard = lazy(() => import('@/components/workflows/WorkflowCard'));
const WorkflowForm = lazy(() => import('@/components/workflows/WorkflowForm'));
const WorkflowExecutionModal = lazy(() => import('@/components/workflows/WorkflowExecutionModal'));

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
  result: WorkflowResult | null;
  error: string | null;
  executed_at: string;
}

// Loading component for Suspense fallback
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8">
    <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
  </div>
);

export default function WorkflowsPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showNewModal, setShowNewModal] = useState(false);
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);

  // State
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [executions, setExecutions] = useState<Record<number, Execution[]>>({});
  const [executing, setExecuting] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'enabled' | 'disabled'>('all');

  // New workflow form state
  const [formName, setFormName] = useState('');
  const [formTrigger, setFormTrigger] = useState<WorkflowTrigger>({
    type: 'manual',
    config: {}
  });
  const [formActions, setFormActions] = useState<WorkflowAction[]>([
    { type: 'send_notification', config: {} }
  ]);
  const [formEnabled, setFormEnabled] = useState(true);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/workflows`);
      if (!response.ok) {
        throw new Error('Failed to fetch workflows');
      }
      const data = await response.json();
      setWorkflows(data.workflows || []);
    } catch (error) {
      console.error('Error fetching workflows:', error);
      setError('Failed to load workflows');
      showToast('Failed to load workflows', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutions = async (workflowId: number) => {
    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}/executions`);
      if (!response.ok) {
        throw new Error('Failed to fetch executions');
      }
      const data = await response.json();
      setExecutions(prev => ({
        ...prev,
        [workflowId]: data.executions || []
      }));
    } catch (error) {
      console.error('Error fetching executions:', error);
      showToast('Failed to load execution history', 'error');
    }
  };

  const createWorkflow = async () => {
    if (!formName.trim()) {
      showToast('Please enter a workflow name', 'error');
      return;
    }

    setCreating(true);
    try {
      const response = await fetch(`${API_URL}/api/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formName,
          trigger: formTrigger,
          actions: formActions,
          enabled: formEnabled
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create workflow');
      }

      const data = await response.json();
      showToast('Workflow created successfully', 'success');
      setShowNewModal(false);
      resetForm();
      fetchWorkflows();
    } catch (error) {
      console.error('Error creating workflow:', error);
      showToast(error instanceof Error ? error.message : 'Failed to create workflow', 'error');
    } finally {
      setCreating(false);
    }
  };

  const executeWorkflow = async (workflow: Workflow) => {
    setExecuting(workflow.id);
    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflow.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          context: {
            manual_execution: true,
            timestamp: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to execute workflow');
      }

      const data = await response.json();
      showToast('Workflow executed successfully', 'success');

      // Create an execution record for display
      const execution: Execution = {
        id: Date.now(),
        workflow_id: workflow.id,
        status: data.status === 'completed' ? 'success' : 'failed',
        result: data.result,
        error: data.error,
        executed_at: new Date().toISOString()
      };

      setSelectedExecution(execution);
      setShowExecutionModal(true);

      // Refresh executions for this workflow
      fetchExecutions(workflow.id);
    } catch (error) {
      console.error('Error executing workflow:', error);
      showToast(error instanceof Error ? error.message : 'Failed to execute workflow', 'error');
    } finally {
      setExecuting(null);
    }
  };

  const deleteWorkflow = async (workflowId: number) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflowId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete workflow');
      }

      showToast('Workflow deleted successfully', 'success');
      fetchWorkflows();
    } catch (error) {
      console.error('Error deleting workflow:', error);
      showToast('Failed to delete workflow', 'error');
    }
  };

  const toggleWorkflow = async (workflow: Workflow) => {
    try {
      const response = await fetch(`${API_URL}/api/workflows/${workflow.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...workflow,
          enabled: !workflow.enabled
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update workflow');
      }

      showToast(`Workflow ${!workflow.enabled ? 'enabled' : 'disabled'}`, 'success');
      fetchWorkflows();
    } catch (error) {
      console.error('Error updating workflow:', error);
      showToast('Failed to update workflow', 'error');
    }
  };

  const toggleExpanded = (workflowId: number) => {
    if (expandedRow === workflowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(workflowId);
      if (!executions[workflowId]) {
        fetchExecutions(workflowId);
      }
    }
  };

  const resetForm = () => {
    setFormName('');
    setFormTrigger({ type: 'manual', config: {} });
    setFormActions([{ type: 'send_notification', config: {} }]);
    setFormEnabled(true);
  };

  // Filter workflows
  const filteredWorkflows = workflows.filter(workflow => {
    const matchesSearch = workflow.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      filterStatus === 'all' ||
      (filterStatus === 'enabled' && workflow.enabled) ||
      (filterStatus === 'disabled' && !workflow.enabled);
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Workflows</h1>
          <p className="text-gray-400">Automate tasks with powerful workflow automation</p>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as 'all' | 'enabled' | 'disabled')}
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Workflows</option>
              <option value="enabled">Enabled Only</option>
              <option value="disabled">Disabled Only</option>
            </select>
          </div>

          {/* New Workflow Button */}
          <button
            onClick={() => setShowNewModal(true)}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-lg text-white font-medium flex items-center gap-2 transition"
          >
            <Plus className="w-5 h-5" />
            New Workflow
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Workflows List */}
        {filteredWorkflows.length === 0 ? (
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
            <h3 className="text-xl font-semibold text-white mb-2">No workflows found</h3>
            <p className="text-gray-400 mb-6">
              {searchQuery ? 'Try adjusting your search criteria' : 'Create your first workflow to get started'}
            </p>
            {!searchQuery && (
              <button
                onClick={() => setShowNewModal(true)}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium inline-flex items-center gap-2"
              >
                <Plus className="w-5 h-5" />
                Create Workflow
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <Suspense fallback={<LoadingSpinner />}>
              {filteredWorkflows.map(workflow => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  isExpanded={expandedRow === workflow.id}
                  isExecuting={executing === workflow.id}
                  executions={executions[workflow.id] || []}
                  onToggleExpand={() => toggleExpanded(workflow.id)}
                  onExecute={() => executeWorkflow(workflow)}
                  onEdit={() => {
                    // TODO: Implement edit functionality
                    showToast('Edit functionality coming soon', 'info');
                  }}
                  onDelete={() => deleteWorkflow(workflow.id)}
                  onToggleEnabled={() => toggleWorkflow(workflow)}
                  onViewDetails={(execution) => {
                    setSelectedExecution(execution);
                    setShowExecutionModal(true);
                  }}
                />
              ))}
            </Suspense>
          </div>
        )}

        {/* New Workflow Modal */}
        {showNewModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
            <div className="bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <Suspense fallback={<LoadingSpinner />}>
                  <WorkflowForm
                    name={formName}
                    trigger={formTrigger}
                    actions={formActions}
                    enabled={formEnabled}
                    isSubmitting={creating}
                    onNameChange={setFormName}
                    onTriggerChange={setFormTrigger}
                    onActionsChange={setFormActions}
                    onEnabledChange={setFormEnabled}
                    onSubmit={createWorkflow}
                    onCancel={() => {
                      setShowNewModal(false);
                      resetForm();
                    }}
                  />
                </Suspense>
              </div>
            </div>
          </div>
        )}

        {/* Execution Modal */}
        {showExecutionModal && (
          <Suspense fallback={<LoadingSpinner />}>
            <WorkflowExecutionModal
              execution={selectedExecution}
              onClose={() => {
                setShowExecutionModal(false);
                setSelectedExecution(null);
              }}
            />
          </Suspense>
        )}
      </div>
    </div>
  );
}