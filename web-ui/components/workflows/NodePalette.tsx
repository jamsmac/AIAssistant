'use client';

import { useMemo, useState } from 'react';
import { Search, RefreshCcw } from 'lucide-react';
import { useWorkflowStore } from './store';
import type { WorkflowNodeType } from './store';

interface NodeTemplate {
  type: WorkflowNodeType;
  label: string;
  description: string;
  icon: string;
}

const NODE_TEMPLATES: NodeTemplate[] = [
  {
    type: 'trigger',
    label: 'Trigger',
    description: 'Starts the workflow',
    icon: '⚡',
  },
  {
    type: 'action',
    label: 'Action',
    description: 'Performs a step',
    icon: '🛠',
  },
  {
    type: 'condition',
    label: 'Condition',
    description: 'Branch logic',
    icon: '🔀',
  },
  {
    type: 'loop',
    label: 'Loop',
    description: 'Repeat actions',
    icon: '🔁',
  },
  {
    type: 'transform',
    label: 'Transform',
    description: 'Modify data',
    icon: '🧠',
  },
];

export function NodePalette() {
  const [search, setSearch] = useState('');
  const addNode = useWorkflowStore(state => state.addNode);
  const reset = useWorkflowStore(state => state.reset);

  const filteredTemplates = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return NODE_TEMPLATES;
    return NODE_TEMPLATES.filter(template =>
      template.label.toLowerCase().includes(term) || template.description.toLowerCase().includes(term),
    );
  }, [search]);

  const handleDragStart = (event: React.DragEvent<HTMLDivElement>, type: WorkflowNodeType) => {
    event.dataTransfer.setData('application/reactflow', type);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleDoubleClick = (type: WorkflowNodeType) => {
    addNode(type, { x: 240, y: 120 });
  };

  return (
    <aside className="flex h-full flex-col gap-4 rounded-xl border border-gray-800 bg-gray-900/80 p-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-300">Node Library</h2>
        <p className="text-xs text-gray-500">Drag nodes onto the canvas or double-click to add</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
        <input
          type="text"
          value={search}
          onChange={event => setSearch(event.target.value)}
          placeholder="Search nodes"
          className="w-full rounded-lg border border-gray-700 bg-gray-800 px-9 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="space-y-3 overflow-y-auto pr-1">
        {filteredTemplates.map(template => (
          <div
            key={template.type}
            draggable
            onDragStart={event => handleDragStart(event, template.type)}
            onDoubleClick={() => handleDoubleClick(template.type)}
            className="group cursor-grab rounded-lg border border-gray-800 bg-gray-800/80 px-3 py-2.5 text-sm transition active:cursor-grabbing hover:border-blue-500/70 hover:bg-blue-500/10"
          >
            <div className="flex items-start gap-3">
              <span className="text-lg" aria-hidden>
                {template.icon}
              </span>
              <div>
                <p className="font-medium text-gray-100 group-hover:text-white">{template.label}</p>
                <p className="text-xs text-gray-400 group-hover:text-gray-300">{template.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto flex flex-col gap-2">
        <button
          type="button"
          onClick={reset}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs font-medium text-gray-300 hover:bg-gray-700"
        >
          <RefreshCcw className="h-4 w-4" />
          Clear Canvas
        </button>
      </div>
    </aside>
  );
}
