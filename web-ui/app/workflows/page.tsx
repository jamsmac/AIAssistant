'use client';

import { useState, useEffect, lazy, Suspense, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import type { WorkflowResult } from '@/types/workflows';
import { Plus, Search, Filter, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/Toast';
import useApi from '@/lib/useApi';

// Lazy load components
const WorkflowCard = lazy(() => import('@/components/workflows/WorkflowCard'));
const WorkflowExecutionModal = lazy(() => import('@/components/workflows/WorkflowExecutionModal'));
const WorkflowBuilderModal = lazy(() =>
  import('@/components/workflows/WorkflowBuilderModal').then(mod => ({ default: mod.WorkflowBuilderModal })),
);

// Types
type WorkflowTrigger = {
  type: string;
  config: Record<string, unknown>;
};

type WorkflowAction = {
  type: string;
  config: Record<string, unknown>;
};

type Workflow = {
  id: number;
  user_id: number;
  name: string;
  trigger: WorkflowTrigger;
  actions: WorkflowAction[];
  enabled: boolean;
  created_at: string;
  last_execution?: string;
};

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
  const api = useApi();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showBuilderModal, setShowBuilderModal] = useState(false);
  const [savingWorkflow, setSavingWorkflow] = useState(false);
  const [showExecutionModal, setShowExecutionModal] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);

  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [executions, setExecutions] = useState<Record<number, Execution[]>>({});
  const [executing, setExecuting] = useState<number | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'enabled' | 'disabled'>('all');

  const fetchWorkflows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<{ workflows?: Workflow[] }>(`/api/workflows`);
      setWorkflows(data.workflows || []);
    } catch (err) {
      console.error('Error fetching workflows:', err);
      setError('Failed to load workflows');
      showToast('Failed to load workflows', 'error');
    } finally {
      setLoading(false);
    }
  }, [api, showToast]);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const fetchExecutions = useCallback(
    async (workflowId: number) => {
      try {
        const data = await api.get<{ executions?: Execution[] }>(`/api/workflows/${workflowId}/executions`);
        setExecutions(prev => ({
          ...prev,
          [workflowId]: data.executions || [],
        }));
      } catch (err) {
        console.error('Error fetching executions:', err);
        showToast('Failed to load execution history', 'error');
      }
    },
    [api, showToast],
  );

  const handleBuilderSave = async ({
    name,
    description,
    enabled,
    builder,
  }: {
    name: string;
    description?: string;
    enabled: boolean;
    builder: {
      trigger?: WorkflowTrigger;
      actions: WorkflowAction[];
      layout: { nodes: any[]; edges: any[] };
    };
  }) => {
    if (!builder.trigger) {
      showToast('Add and configure a trigger before saving', 'error');
      return;
    }
    if (builder.actions.length === 0) {
      showToast('Add at least one action before saving', 'error');
      return;
    }

    setSavingWorkflow(true);
    try {
      await api.post(`/api/workflows`, {
        name,
        description,
        enabled,
        trigger: builder.trigger,
        actions: builder.actions,
        layout: builder.layout,
      });

      showToast('Workflow created successfully', 'success');
      setShowBuilderModal(false);
      fetchWorkflows();
    } catch (err) {
      console.error('Error creating workflow:', err);
      showToast(err instanceof Error ? err.message : 'Failed to create workflow', 'error');
      throw err;
    } finally {
      setSavingWorkflow(false);
    }
  };

  const executeWorkflow = async (workflow: Workflow) => {
    setExecuting(workflow.id);
    try {
      const data = await api.post<{ status?: string; result?: WorkflowResult | null; error?: string | null }>(
        `/api/workflows/${workflow.id}/execute`,
        {
          context: {
            manual_execution: true,
            timestamp: new Date().toISOString(),
          },
        },
      );
      showToast('Workflow executed successfully', 'success');

      const execution: Execution = {
        id: Date.now(),
        workflow_id: workflow.id,
        status: data.status === 'completed' ? 'success' : 'failed',
        result: data.result || null,
        error: data.error,
        executed_at: new Date().toISOString(),
      };

      setSelectedExecution(execution);
      setShowExecutionModal(true);
      fetchExecutions(workflow.id);
    } catch (err) {
      console.error('Error executing workflow:', err);
      showToast(err instanceof Error ? err.message : 'Failed to execute workflow', 'error');
    } finally {
      setExecuting(null);
    }
  };

  const deleteWorkflow = async (workflowId: number) => {
    if (!confirm('Are you sure you want to delete this workflow?')) return;

    try {
      await api.delete(`/api/workflows/${workflowId}`);

      showToast('Workflow deleted successfully', 'success');
      fetchWorkflows();
    } catch (err) {
      console.error('Error deleting workflow:', err);
      showToast('Failed to delete workflow', 'error');
    }
  };

  const toggleWorkflow = async (workflow: Workflow) => {
    try {
      await api.put(`/api/workflows/${workflow.id}`, {
        ...workflow,
        enabled: !workflow.enabled,
      });

      showToast(`Workflow ${!workflow.enabled ? 'enabled' : 'disabled'}`, 'success');
      fetchWorkflows();
    } catch (err) {
      console.error('Error updating workflow:', err);
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
              onChange={event => setSearchQuery(event.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filterStatus}
              onChange={event => setFilterStatus(event.target.value as 'all' | 'enabled' | 'disabled')}
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Workflows</option>
              <option value="enabled">Enabled Only</option>
              <option value="disabled">Disabled Only</option>
            </select>
          </div>

          {/* New Workflow Button */}
          <button
            onClick={() => setShowBuilderModal(true)}
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
                onClick={() => setShowBuilderModal(true)}
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
                    showToast('Edit functionality coming soon', 'info');
                  }}
                  onDelete={() => deleteWorkflow(workflow.id)}
                  onToggleEnabled={() => toggleWorkflow(workflow)}
                  onViewDetails={execution => {
                    setSelectedExecution(execution);
                    setShowExecutionModal(true);
                  }}
                />
              ))}
            </Suspense>
          </div>
        )}
      </div>

      <Suspense fallback={<LoadingSpinner />}>
        <WorkflowBuilderModal
          open={showBuilderModal}
          onClose={() => setShowBuilderModal(false)}
          onSave={handleBuilderSave}
          isSaving={savingWorkflow}
        />
      </Suspense>

      {showExecutionModal && selectedExecution && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-gray-900 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <Suspense fallback={<LoadingSpinner />}>
                <WorkflowExecutionModal
                  execution={selectedExecution}
                  onClose={() => {
                    setShowExecutionModal(false);
                    setSelectedExecution(null);
                  }}
                />
              </Suspense>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}