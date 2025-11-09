"use client";

import React, { Suspense, useCallback, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import type { ReactFlowInstance } from 'reactflow';
import { ReactFlowProvider } from 'reactflow';
import { Loader2 } from 'lucide-react';
import { shallow } from 'zustand/shallow';

const ReactFlow = dynamic(() => import('reactflow').then(mod => mod.default), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
    </div>
  ),
});
const Background = dynamic(() => import('reactflow').then(mod => mod.Background), { ssr: false });
const Controls = dynamic(() => import('reactflow').then(mod => mod.Controls), { ssr: false });
const MiniMap = dynamic(() => import('reactflow').then(mod => mod.MiniMap), { ssr: false });

import type { NodeTypes } from 'reactflow';
import type { WorkflowBuildResult, WorkflowValidationError, WorkflowNodeType } from './store';
import { useWorkflowStore } from './store';
import { NodePalette } from './NodePalette';
import { NodeConfigPanel } from './NodeConfigPanel';
import { WorkflowPreview } from './WorkflowPreview';
import { TriggerNode, ActionNode, ConditionNode, LoopNode, TransformNode } from './nodes';
import { useToast } from '@/components/ui/Toast';

import 'reactflow/dist/style.css';

export interface WorkflowBuilderProps {
  onSave: (data: WorkflowBuildResult) => Promise<void> | void;
  isSaving?: boolean;
}

export function WorkflowBuilder({ onSave, isSaving }: WorkflowBuilderProps) {
  const [previewMode, setPreviewMode] = useState(false);
  const [validationErrors, setValidationErrors] = useState<WorkflowValidationError[]>([]);
  const flowWrapperRef = useRef<HTMLDivElement | null>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const { showToast } = useToast();

  const [
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    setSelectedNode,
    selectedNodeId,
    reset,
    toWorkflow,
    clearNodeErrors,
    setReactFlowInstanceStore,
  ] = useWorkflowStore(
    state => [
      state.nodes,
      state.edges,
      state.onNodesChange,
      state.onEdgesChange,
      state.onConnect,
      state.addNode,
      state.setSelectedNode,
      state.selectedNodeId,
      state.reset,
      state.toWorkflow,
      state.clearNodeErrors,
      state.setReactFlowInstance,
    ],
    shallow,
  );

  const nodeTypes: NodeTypes = useMemo(
    () => ({
      trigger: TriggerNode,
      action: ActionNode,
      condition: ConditionNode,
      loop: LoopNode,
      transform: TransformNode,
    }),
    [],
  );

  const handleInit = useCallback(
    (instance: ReactFlowInstance) => {
      setReactFlowInstance(instance);
      setReactFlowInstanceStore(instance);
    },
    [setReactFlowInstanceStore],
  );

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow') as WorkflowNodeType;
      if (!type || !reactFlowInstance) return;
      const bounds = flowWrapperRef.current?.getBoundingClientRect();
      const position = reactFlowInstance.project({
        x: event.clientX - (bounds?.left ?? 0),
        y: event.clientY - (bounds?.top ?? 0),
      });
      addNode(type, position);
    },
    [reactFlowInstance, addNode],
  );

  const handleSave = useCallback(async () => {
    const result = toWorkflow();
    setValidationErrors(result.errors);
    if (result.errors.length > 0) {
      const firstError = result.errors[0];
      showToast(firstError?.message ?? 'Please resolve validation issues', 'error');
      return;
    }
    try {
      await onSave(result);
    } catch {
      /* parent handles error feedback */
    }
  }, [onSave, toWorkflow, showToast]);

  const clearCanvas = useCallback(() => {
    reset();
    setValidationErrors([]);
    clearNodeErrors();
  }, [reset, clearNodeErrors]);

  return (
    <ReactFlowProvider>
      <div className="grid h-full min-h-[640px] grid-cols-[240px,1fr,320px] gap-4">
        <NodePalette />

        <div
          ref={flowWrapperRef}
          className="relative rounded-xl border border-gray-800 bg-gray-950/70"
        >
          <Suspense
            fallback={
              <div className="flex h-full items-center justify-center">
                <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
              </div>
            }
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={handleInit}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onNodeClick={(_, node) => setSelectedNode(node.id)}
              onNodesDelete={deletedNodes => {
                if (deletedNodes.some(node => node.id === selectedNodeId)) {
                  setSelectedNode(null);
                }
              }}
              onPaneClick={() => setSelectedNode(null)}
              fitView
              proOptions={{ hideAttribution: true }}
              className="workflow-builder-flow"
              minZoom={0.5}
              maxZoom={1.5}
            >
              <Background variant="dots" gap={16} size={1} className="opacity-50" />
              <Controls className="!bg-gray-900 !border-gray-800" />
              <MiniMap
                pannable
                zoomable
                className="!bg-gray-950 !border-none"
                maskColor="rgba(12,10,24,0.65)"
                nodeColor={node => {
                  switch (node.type) {
                    case 'trigger':
                      return '#60A5FA';
                    case 'action':
                      return '#F97316';
                    case 'condition':
                      return '#FACC15';
                    case 'loop':
                      return '#34D399';
                    case 'transform':
                      return '#A855F7';
                    default:
                      return '#94A3B8';
                  }
                }}
              />
            </ReactFlow>
          </Suspense>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setPreviewMode(previous => !previous)}
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-700"
              >
                {previewMode ? 'Exit Preview' : 'Preview Execution'}
              </button>
              <button
                type="button"
                onClick={clearCanvas}
                className="rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-200 hover:bg-gray-700"
              >
                Reset
              </button>
            </div>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-1.5 text-sm font-medium text-white shadow-lg transition hover:from-blue-600 hover:to-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving ? 'Saving...' : 'Save Workflow'}
            </button>
          </div>

          {validationErrors.length > 0 && (
            <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-xs text-yellow-200">
              <p className="font-medium">Validation Issues</p>
              <ul className="mt-1 list-disc space-y-1 pl-4">
                {validationErrors.map((error, index) => (
                  <li key={`${error.nodeId ?? 'global'}-${index}`}>{error.message}</li>
                ))}
              </ul>
            </div>
          )}

          {previewMode ? <WorkflowPreview /> : <NodeConfigPanel />}
        </div>
      </div>
    </ReactFlowProvider>
  );
}
