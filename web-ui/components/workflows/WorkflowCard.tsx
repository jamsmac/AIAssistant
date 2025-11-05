'use client';

import React, { memo } from 'react';
import {
  Play, Edit2, Trash2, ChevronDown, ChevronUp,
  Clock, Zap, Webhook, Mail, Database as DatabaseIcon,
  Check, AlertCircle, CheckCircle2, Loader2
} from 'lucide-react';

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

interface WorkflowCardProps {
  workflow: Workflow;
  isExpanded: boolean;
  isExecuting: boolean;
  executions: Execution[];
  onToggleExpand: () => void;
  onExecute: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onToggleEnabled: () => void;
  onViewDetails: (execution: Execution) => void;
}

const TRIGGER_ICONS = {
  manual: Play,
  schedule: Clock,
  webhook: Webhook,
  email_received: Mail,
  record_created: DatabaseIcon,
};

const TRIGGER_COLORS = {
  manual: 'blue',
  schedule: 'purple',
  webhook: 'green',
  email_received: 'orange',
  record_created: 'pink',
};

const WorkflowCard = memo(function WorkflowCard({
  workflow,
  isExpanded,
  isExecuting,
  executions,
  onToggleExpand,
  onExecute,
  onEdit,
  onDelete,
  onToggleEnabled,
  onViewDetails
}: WorkflowCardProps) {
  const TriggerIcon = TRIGGER_ICONS[workflow.trigger.type] || Zap;
  const triggerColor = TRIGGER_COLORS[workflow.trigger.type] || 'gray';

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 bg-${triggerColor}-500/20 rounded-lg flex items-center justify-center`}>
              <TriggerIcon className={`w-6 h-6 text-${triggerColor}-500`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">{workflow.name}</h3>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-400">
                <span className="flex items-center gap-1">
                  <TriggerIcon className="w-4 h-4" />
                  {workflow.trigger.type.replace('_', ' ')}
                </span>
                <span>{workflow.actions.length} actions</span>
                {workflow.last_execution && (
                  <span>Last run: {formatDate(workflow.last_execution)}</span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Enable/Disable Toggle */}
            <button
              onClick={onToggleEnabled}
              className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                workflow.enabled
                  ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                  : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
              }`}
            >
              {workflow.enabled ? 'Enabled' : 'Disabled'}
            </button>

            {/* Action Buttons */}
            {workflow.trigger.type === 'manual' && (
              <button
                onClick={onExecute}
                disabled={isExecuting || !workflow.enabled}
                className="p-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg text-white transition"
                title="Execute workflow"
              >
                {isExecuting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
              </button>
            )}
            <button
              onClick={onEdit}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition"
              title="Edit workflow"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={onDelete}
              className="p-2 bg-gray-700 hover:bg-red-600 rounded-lg text-white transition"
              title="Delete workflow"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={onToggleExpand}
              className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>

        {/* Actions Summary */}
        <div className="flex flex-wrap gap-2">
          {workflow.actions.map((action, index) => (
            <div
              key={index}
              className="px-3 py-1 bg-gray-700 rounded-lg text-xs text-gray-300"
            >
              {action.type.replace('_', ' ')}
            </div>
          ))}
        </div>

        {/* Trigger Config */}
        {workflow.trigger.type !== 'manual' && workflow.trigger.config && (
          <div className="mt-4 p-3 bg-gray-900/50 rounded-lg">
            <div className="text-xs text-gray-400 mb-1">Trigger Configuration</div>
            <pre className="text-xs text-gray-300 whitespace-pre-wrap">
              {JSON.stringify(workflow.trigger.config, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Expanded Executions */}
      {isExpanded && (
        <div className="border-t border-gray-700 p-6">
          <h4 className="text-sm font-medium text-white mb-4">Execution History</h4>
          {executions.length === 0 ? (
            <p className="text-gray-400 text-sm">No executions yet</p>
          ) : (
            <div className="space-y-2">
              {executions.slice(0, 5).map(execution => (
                <div
                  key={execution.id}
                  className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg cursor-pointer hover:bg-gray-900/70 transition"
                  onClick={() => onViewDetails(execution)}
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <div className="text-sm text-white">
                        {execution.status === 'success' ? 'Completed' : 'Failed'}
                      </div>
                      <div className="text-xs text-gray-400">
                        {formatDate(execution.executed_at)}
                      </div>
                    </div>
                  </div>
                  {execution.error && (
                    <div className="text-xs text-red-400 max-w-xs truncate">
                      {execution.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
});

export default WorkflowCard;