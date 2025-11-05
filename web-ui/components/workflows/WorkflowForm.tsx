'use client';

import React, { memo, useState } from 'react';
import { Plus, Trash2, X } from 'lucide-react';

interface WorkflowTrigger {
  type: 'manual' | 'schedule' | 'webhook' | 'email_received' | 'record_created';
  config: Record<string, any>;
}

interface WorkflowAction {
  type: string;
  config: Record<string, any>;
}

interface WorkflowFormProps {
  name: string;
  trigger: WorkflowTrigger;
  actions: WorkflowAction[];
  enabled: boolean;
  isSubmitting: boolean;
  onNameChange: (name: string) => void;
  onTriggerChange: (trigger: WorkflowTrigger) => void;
  onActionsChange: (actions: WorkflowAction[]) => void;
  onEnabledChange: (enabled: boolean) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

const TRIGGER_TYPES = [
  { value: 'manual', label: 'Manual' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'webhook', label: 'Webhook' },
  { value: 'email_received', label: 'Email Received' },
  { value: 'record_created', label: 'Record Created' },
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

const WorkflowForm = memo(function WorkflowForm({
  name,
  trigger,
  actions,
  enabled,
  isSubmitting,
  onNameChange,
  onTriggerChange,
  onActionsChange,
  onEnabledChange,
  onSubmit,
  onCancel
}: WorkflowFormProps) {
  const handleTriggerTypeChange = (type: string) => {
    onTriggerChange({
      type: type as WorkflowTrigger['type'],
      config: {}
    });
  };

  const handleTriggerConfigChange = (field: string, value: any) => {
    onTriggerChange({
      ...trigger,
      config: {
        ...trigger.config,
        [field]: value
      }
    });
  };

  const handleActionTypeChange = (index: number, type: string) => {
    const newActions = [...actions];
    newActions[index] = { type, config: {} };
    onActionsChange(newActions);
  };

  const handleActionConfigChange = (index: number, field: string, value: any) => {
    const newActions = [...actions];
    newActions[index] = {
      ...newActions[index],
      config: {
        ...newActions[index].config,
        [field]: value
      }
    };
    onActionsChange(newActions);
  };

  const addAction = () => {
    onActionsChange([...actions, { type: 'send_notification', config: {} }]);
  };

  const removeAction = (index: number) => {
    onActionsChange(actions.filter((_, i) => i !== index));
  };

  const renderTriggerConfig = () => {
    switch (trigger.type) {
      case 'schedule':
        return (
          <div className="space-y-3 mt-3">
            <input
              type="text"
              placeholder="Cron expression (e.g., 0 0 * * *)"
              value={trigger.config.cron || ''}
              onChange={(e) => handleTriggerConfigChange('cron', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            />
          </div>
        );
      case 'webhook':
        return (
          <div className="mt-3 p-3 bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-300">Webhook URL will be generated after creation</p>
          </div>
        );
      case 'email_received':
        return (
          <div className="space-y-3 mt-3">
            <input
              type="text"
              placeholder="From address filter (optional)"
              value={trigger.config.from_filter || ''}
              onChange={(e) => handleTriggerConfigChange('from_filter', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            />
            <input
              type="text"
              placeholder="Subject filter (optional)"
              value={trigger.config.subject_filter || ''}
              onChange={(e) => handleTriggerConfigChange('subject_filter', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            />
          </div>
        );
      case 'record_created':
        return (
          <div className="space-y-3 mt-3">
            <input
              type="text"
              placeholder="Database ID"
              value={trigger.config.database_id || ''}
              onChange={(e) => handleTriggerConfigChange('database_id', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white"
            />
          </div>
        );
      default:
        return null;
    }
  };

  const renderActionConfig = (action: WorkflowAction, index: number) => {
    const actionType = ACTION_TYPES.find(t => t.value === action.type);
    if (!actionType) return null;

    return (
      <div className="space-y-3 mt-3">
        {actionType.fields.map(field => (
          <div key={field}>
            <label className="block text-xs text-gray-400 mb-1 capitalize">
              {field.replace('_', ' ')}
            </label>
            {field === 'body' || field === 'data' || field === 'payload' || field === 'context' ? (
              <textarea
                placeholder={`Enter ${field}`}
                value={action.config[field] || ''}
                onChange={(e) => handleActionConfigChange(index, field, e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white text-sm"
                rows={3}
              />
            ) : (
              <input
                type="text"
                placeholder={`Enter ${field}`}
                value={action.config[field] || ''}
                onChange={(e) => handleActionConfigChange(index, field, e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white text-sm"
              />
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold text-white">Workflow Configuration</h3>
        <button
          onClick={onCancel}
          className="p-2 hover:bg-gray-700 rounded-lg transition"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Workflow Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Enter workflow name"
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
        />
      </div>

      {/* Trigger */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Trigger Type
        </label>
        <select
          value={trigger.type}
          onChange={(e) => handleTriggerTypeChange(e.target.value)}
          className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-white"
        >
          {TRIGGER_TYPES.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        {renderTriggerConfig()}
      </div>

      {/* Actions */}
      <div>
        <div className="flex justify-between items-center mb-3">
          <label className="text-sm font-medium text-gray-300">
            Actions ({actions.length})
          </label>
          <button
            onClick={addAction}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm flex items-center gap-1"
          >
            <Plus className="w-4 h-4" />
            Add Action
          </button>
        </div>

        <div className="space-y-4">
          {actions.map((action, index) => (
            <div key={index} className="p-4 bg-gray-800 rounded-lg border border-gray-700">
              <div className="flex justify-between items-start mb-3">
                <select
                  value={action.type}
                  onChange={(e) => handleActionTypeChange(index, e.target.value)}
                  className="flex-1 mr-2 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
                >
                  {ACTION_TYPES.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeAction(index)}
                  className="p-2 hover:bg-red-600 bg-gray-700 rounded-lg transition"
                >
                  <Trash2 className="w-4 h-4 text-white" />
                </button>
              </div>
              {renderActionConfig(action, index)}
            </div>
          ))}
        </div>
      </div>

      {/* Enabled */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="enabled"
          checked={enabled}
          onChange={(e) => onEnabledChange(e.target.checked)}
          className="w-4 h-4 text-blue-600"
        />
        <label htmlFor="enabled" className="text-sm text-gray-300">
          Enable workflow immediately
        </label>
      </div>

      {/* Submit */}
      <div className="flex gap-3">
        <button
          onClick={onSubmit}
          disabled={isSubmitting || !name}
          className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg text-white font-medium transition"
        >
          {isSubmitting ? 'Creating...' : 'Create Workflow'}
        </button>
        <button
          onClick={onCancel}
          className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg text-white font-medium transition"
        >
          Cancel
        </button>
      </div>
    </div>
  );
});

export default WorkflowForm;