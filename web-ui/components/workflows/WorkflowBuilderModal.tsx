'use client';

import { useState, useCallback } from 'react';
import { X } from 'lucide-react';
import { WorkflowBuilder } from './WorkflowBuilder';
import type { WorkflowBuildResult } from './store';
import { useWorkflowStore } from './store';

interface WorkflowBuilderModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (payload: {
    name: string;
    description?: string;
    enabled: boolean;
    builder: WorkflowBuildResult;
  }) => Promise<void> | void;
  isSaving?: boolean;
}

export function WorkflowBuilderModal({ open, onClose, onSave, isSaving }: WorkflowBuilderModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const resetBuilderState = useCallback(() => {
    const store = useWorkflowStore.getState();
    store.resetAll();
  }, []);

  const handleClose = () => {
    resetBuilderState();
    setName('');
    setDescription('');
    setEnabled(true);
    setError(null);
    onClose();
  };

  const handleSave = async (builder: WorkflowBuildResult) => {
    if (!name.trim()) {
      setError('Workflow name is required');
      return;
    }
    setError(null);
    try {
      await onSave({
        name: name.trim(),
        description: description.trim() || undefined,
        enabled,
        builder,
      });
      resetBuilderState();
      setName('');
      setDescription('');
      setEnabled(true);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to save workflow');
      }
      throw err;
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-6">
      <div className="flex w-full max-w-6xl flex-col gap-4 rounded-2xl border border-gray-800 bg-[#0B0B12] p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Visual Workflow Builder</h2>
            <p className="text-sm text-gray-400">Design complex workflows with drag-and-drop simplicity</p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 rounded-xl border border-gray-800 bg-gray-900/60 p-4 text-sm sm:grid-cols-3">
          <label className="flex flex-col gap-1 sm:col-span-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">Workflow Name</span>
            <input
              type="text"
              value={name}
              onChange={event => setName(event.target.value)}
              placeholder="My automation"
              className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>
          <label className="flex flex-col gap-1 sm:col-span-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">Description</span>
            <textarea
              value={description}
              onChange={event => setDescription(event.target.value)}
              placeholder="Describe what this workflow accomplishes"
              rows={2}
              className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-200">
            <input
              type="checkbox"
              checked={enabled}
              onChange={event => setEnabled(event.target.checked)}
              className="h-4 w-4 text-blue-500"
            />
            Enable workflow immediately after saving
          </label>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="min-h-[640px]">
          <WorkflowBuilder onSave={handleSave} isSaving={isSaving} />
        </div>
      </div>
    </div>
  );
}
