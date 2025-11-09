'use client';

import { useMemo, useState, useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { shallow } from 'zustand/shallow';
import { useWorkflowStore } from './store';

export function WorkflowPreview() {
  const [nodes, edges] = useWorkflowStore(state => [state.nodes, state.edges], shallow);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const path = useMemo(() => {
    if (nodes.length === 0) return [] as string[];
    const trigger = nodes.find(node => node.type === 'trigger');
    if (!trigger) return [];

    const adjacency: Record<string, string[]> = {};
    edges.forEach(edge => {
      adjacency[edge.source] = adjacency[edge.source] ?? [];
      adjacency[edge.source].push(edge.target);
    });

    const ordered: string[] = [trigger.id];
    const queue: string[] = [...(adjacency[trigger.id] ?? [])];
    const visited = new Set<string>([trigger.id]);

    while (queue.length) {
      const id = queue.shift()!;
      if (visited.has(id)) continue;
      ordered.push(id);
      visited.add(id);
      (adjacency[id] ?? []).forEach(nextId => queue.push(nextId));
    }

    return ordered;
  }, [nodes, edges]);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (isPlaying && path.length > 0) {
      timer = setTimeout(() => {
        setActiveIndex(current => {
          const next = (current ?? -1) + 1;
          if (next >= path.length) {
            setIsPlaying(false);
            return path.length - 1;
          }
          return next;
        });
      }, 1200);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isPlaying, path, activeIndex]);

  const startSimulation = () => {
    if (path.length === 0) return;
    setActiveIndex(0);
    setIsPlaying(true);
  };

  const stopSimulation = () => {
    setIsPlaying(false);
  };

  const resetSimulation = () => {
    setIsPlaying(false);
    setActiveIndex(null);
  };

  const renderStepLabel = (nodeId: string, index: number) => {
    const node = nodes.find(item => item.id === nodeId);
    if (!node) return `Unknown node ${index + 1}`;
    const prefix = node.type === 'trigger' ? 'Trigger' : node.type === 'action' ? 'Action' : node.type;
    return `${index + 1}. ${prefix}: ${node.data.label ?? ''}`;
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/70 p-4 text-sm text-gray-200">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-100">Execution Preview</h3>
          <p className="text-xs text-gray-400">Simulate the order of execution for this workflow</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={isPlaying ? stopSimulation : startSimulation}
            disabled={path.length === 0}
            className="inline-flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPlaying ? (
              <>
                <Pause className="w-3.5 h-3.5" /> Pause
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5" /> Simulate
              </>
            )}
          </button>
          <button
            type="button"
            onClick={resetSimulation}
            className="inline-flex items-center gap-1 rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-700"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>
        </div>
      </div>

      {path.length === 0 ? (
        <p className="text-xs text-gray-500">Add a trigger and connect nodes to preview execution.</p>
      ) : (
        <ol className="space-y-2 text-xs">
          {path.map((nodeId, index) => (
            <li
              key={nodeId}
              className={[
                'rounded-lg border px-3 py-2 transition',
                index === activeIndex
                  ? 'border-blue-500/50 bg-blue-500/10 text-blue-200'
                  : 'border-gray-800 bg-gray-800/60 text-gray-300',
              ].join(' ')}
            >
              {renderStepLabel(nodeId, index)}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
