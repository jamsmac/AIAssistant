'use client';

import { useMemo } from 'react';
import { shallow } from 'zustand/shallow';
import { useWorkflowStore } from './store';
import type { WorkflowNodeType } from './store';

const TRIGGER_OPTIONS = [
  { value: 'manual', label: 'Manual' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'email_received', label: 'Email Received' },
  { value: 'record_created', label: 'Record Created' },
];

const ACTION_OPTIONS = [
  { value: 'send_email', label: 'Send Email', fields: ['to', 'subject', 'body'] },
  { value: 'create_record', label: 'Create Record', fields: ['database_id', 'data'] },
  { value: 'update_record', label: 'Update Record', fields: ['record_id', 'database_id', 'data'] },
  { value: 'delete_record', label: 'Delete Record', fields: ['record_id', 'database_id'] },
  { value: 'call_webhook', label: 'Call Webhook', fields: ['url', 'payload'] },
  { value: 'run_ai_agent', label: 'Run AI Agent', fields: ['prompt', 'task_type'] },
  { value: 'send_notification', label: 'Send Notification', fields: ['message', 'level'] },
  { value: 'send_telegram', label: 'Send Telegram', fields: ['chat_id', 'message'] },
  { value: 'execute_workflow', label: 'Execute Workflow', fields: ['workflow_id', 'context'] },
];

function TextInput({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm text-gray-300">
      <span className="text-xs uppercase tracking-wide text-gray-400">{label}</span>
      <input
        type={type}
        value={value}
        onChange={event => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
}: {
  label: string;
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  rows?: number;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm text-gray-300">
      <span className="text-xs uppercase tracking-wide text-gray-400">{label}</span>
      <textarea
        value={value}
        onChange={event => onChange(event.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </label>
  );
}

export function NodeConfigPanel() {
  const [selectedNodeId, nodes, updateNodeData] = useWorkflowStore(
    state => [state.selectedNodeId, state.nodes, state.updateNodeData],
    shallow,
  );

  const selectedNode = useMemo(() => nodes.find(node => node.id === selectedNodeId), [nodes, selectedNodeId]);

  if (!selectedNode) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/70 p-6 text-sm text-gray-400">
        Select a node to configure its details
      </div>
    );
  }

  const config = (selectedNode.data.config ?? {}) as Record<string, any>;

  const handleConfigChange = (field: string, value: unknown) => {
    updateNodeData(selectedNode.id, {
      config: {
        ...config,
        [field]: value,
      },
    });
  };

  const handleLabelChange = (value: string) => {
    updateNodeData(selectedNode.id, {
      label: value,
    });
  };

  const handleDescriptionChange = (value: string) => {
    updateNodeData(selectedNode.id, {
      description: value,
    });
  };

  const renderTriggerConfig = () => {
    const triggerType = (config.triggerType as string) ?? 'manual';
    return (
      <div className="space-y-3">
        <label className="flex flex-col gap-1 text-sm text-gray-300">
          <span className="text-xs uppercase tracking-wide text-gray-400">Trigger Type</span>
          <select
            value={triggerType}
            onChange={event => handleConfigChange('triggerType', event.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {TRIGGER_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {triggerType === 'schedule' && (
          <>
            <TextInput
              label="Cron Expression"
              value={config.cron ?? ''}
              onChange={value => handleConfigChange('cron', value)}
              placeholder="0 0 * * *"
            />
            <TextInput
              label="Timezone"
              value={config.timezone ?? ''}
              onChange={value => handleConfigChange('timezone', value)}
              placeholder="UTC"
            />
          </>
        )}

        {triggerType === 'webhook' && (
          <TextInput
            label="Webhook Secret"
            value={config.secret ?? ''}
            onChange={value => handleConfigChange('secret', value)}
            placeholder="Optional secret to verify requests"
          />
        )}

        {triggerType === 'email_received' && (
          <>
            <TextInput
              label="From Filter"
              value={config.from_filter ?? ''}
              onChange={value => handleConfigChange('from_filter', value)}
              placeholder="example@domain.com"
            />
            <TextInput
              label="Subject Filter"
              value={config.subject_filter ?? ''}
              onChange={value => handleConfigChange('subject_filter', value)}
              placeholder="Invoice"
            />
          </>
        )}

        {triggerType === 'record_created' && (
          <TextInput
            label="Database ID"
            value={config.database_id ?? ''}
            onChange={value => handleConfigChange('database_id', value)}
            placeholder="database-123"
          />
        )}
      </div>
    );
  };

  const renderActionConfig = () => {
    const actionType = (config.actionType as string) ?? 'send_email';
    const option = ACTION_OPTIONS.find(item => item.value === actionType) ?? ACTION_OPTIONS[0];
    return (
      <div className="space-y-3">
        <label className="flex flex-col gap-1 text-sm text-gray-300">
          <span className="text-xs uppercase tracking-wide text-gray-400">Action Type</span>
          <select
            value={actionType}
            onChange={event => handleConfigChange('actionType', event.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {ACTION_OPTIONS.map(item => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        {option.fields.map(field => (
          field === 'body' || field === 'payload' || field === 'data' || field === 'context' ? (
            <TextArea
              key={field}
              label={field.replace('_', ' ')}
              value={(config[field] as string) ?? ''}
              onChange={value => handleConfigChange(field, value)}
              placeholder={`Enter ${field}`}
            />
          ) : (
            <TextInput
              key={field}
              label={field.replace('_', ' ')}
              value={(config[field] as string) ?? ''}
              onChange={value => handleConfigChange(field, value)}
              placeholder={`Enter ${field}`}
            />
          )
        ))}
      </div>
    );
  };

  const renderConditionConfig = () => (
    <TextArea
      label="Condition Expression"
      value={(config.expression as string) ?? ''}
      onChange={value => handleConfigChange('expression', value)}
      placeholder="order.total > 100"
    />
  );

  const renderLoopConfig = () => (
    <div className="space-y-3">
      <TextInput
        label="Iterations"
        value={String(config.iterations ?? 3)}
        onChange={value => handleConfigChange('iterations', Number(value) || 1)}
        type="number"
      />
      <TextInput
        label="Iteration Variable"
        value={(config.variable as string) ?? 'item'}
        onChange={value => handleConfigChange('variable', value)}
      />
    </div>
  );

  const renderTransformConfig = () => (
    <TextArea
      label="Transform Script"
      value={(config.script as string) ?? ''}
      onChange={value => handleConfigChange('script', value)}
      placeholder="// return transformed data\nreturn input;"
      rows={8}
    />
  );

  const renderConfigByType = () => {
    switch (selectedNode.type as WorkflowNodeType) {
      case 'trigger':
        return renderTriggerConfig();
      case 'action':
        return renderActionConfig();
      case 'condition':
        return renderConditionConfig();
      case 'loop':
        return renderLoopConfig();
      case 'transform':
        return renderTransformConfig();
      default:
        return null;
    }
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/70 p-4 text-sm text-gray-200 space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-100">Node Configuration</h3>
        <p className="text-xs text-gray-400">Adjust properties for the selected node</p>
      </div>

      <div className="space-y-3">
        <TextInput
          label="Label"
          value={selectedNode.data.label ?? ''}
          onChange={handleLabelChange}
          placeholder="Enter display label"
        />
        <TextArea
          label="Description"
          value={selectedNode.data.description ?? ''}
          onChange={handleDescriptionChange}
          placeholder="Optional description"
          rows={3}
        />
      </div>

      <div className="space-y-4">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-400">Specific Settings</h4>
        {renderConfigByType() ?? (
          <p className="text-xs text-gray-500">No additional settings for this node type.</p>
        )}
      </div>

      {selectedNode.data.errors && selectedNode.data.errors.length > 0 && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200">
          <p className="font-medium">Validation Issues</p>
          <ul className="list-disc pl-4">
            {selectedNode.data.errors.map(error => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
