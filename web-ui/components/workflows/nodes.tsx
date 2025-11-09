'use client';

import { memo } from 'react';
import type { ReactNode } from 'react';
import type { NodeProps } from 'reactflow';
import { Handle, Position } from 'reactflow';
import type { WorkflowNodeData } from './store';

function NodeContainer({
  children,
  selected,
  accent,
  errors,
}: {
  children: ReactNode;
  selected?: boolean;
  accent: string;
  errors?: string[];
}) {
  return (
    <div
      className={[
        'min-w-[180px] max-w-[240px] rounded-xl border px-4 py-3 shadow-md transition-all duration-150',
        'bg-gray-900/95 text-white backdrop-blur-sm',
        selected ? 'ring-2 ring-offset-2 ring-offset-gray-950 ring-blue-500 border-blue-400' : 'border-gray-700/60',
      ].join(' ')}
      style={{ boxShadow: selected ? '0 10px 30px rgba(59, 130, 246, 0.2)' : undefined }}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg" aria-hidden>
          {accent}
        </span>
        {children}
      </div>
      {errors && errors.length > 0 && (
        <div className="mt-2 rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-300">
          {errors.map(error => (
            <div key={error}>{error}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function NodeTitle({ title, description }: { title: string; description?: string }) {
  return (
    <div>
      <p className="text-sm font-semibold leading-tight">{title}</p>
      {description && <p className="text-xs text-gray-400 mt-0.5">{description}</p>}
    </div>
  );
}

export const TriggerNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <NodeContainer selected={selected} accent="⚡" errors={data.errors}>
      <NodeTitle title={data.label ?? 'Trigger'} description={data.description} />
      <Handle type="source" position={Position.Bottom} className="!bg-blue-400" />
    </NodeContainer>
  );
});
TriggerNode.displayName = 'TriggerNode';

export const ActionNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <NodeContainer selected={selected} accent="🛠" errors={data.errors}>
      <NodeTitle title={data.label ?? 'Action'} description={data.description} />
      <Handle type="target" position={Position.Top} className="!bg-orange-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-orange-400" />
    </NodeContainer>
  );
});
ActionNode.displayName = 'ActionNode';

export const ConditionNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <NodeContainer selected={selected} accent="🔀" errors={data.errors}>
      <NodeTitle title={data.label ?? 'Condition'} description={data.description} />
      <Handle type="target" position={Position.Top} className="!bg-yellow-400" />
      <Handle id="true" type="source" position={Position.Left} className="!bg-yellow-400" />
      <Handle id="false" type="source" position={Position.Right} className="!bg-yellow-400" />
    </NodeContainer>
  );
});
ConditionNode.displayName = 'ConditionNode';

export const LoopNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <NodeContainer selected={selected} accent="🔁" errors={data.errors}>
      <NodeTitle title={data.label ?? 'Loop'} description={data.description} />
      <Handle type="target" position={Position.Top} className="!bg-green-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-green-400" />
    </NodeContainer>
  );
});
LoopNode.displayName = 'LoopNode';

export const TransformNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <NodeContainer selected={selected} accent="🧠" errors={data.errors}>
      <NodeTitle title={data.label ?? 'Transform'} description={data.description} />
      <Handle type="target" position={Position.Top} className="!bg-purple-400" />
      <Handle type="source" position={Position.Bottom} className="!bg-purple-400" />
    </NodeContainer>
  );
});
TransformNode.displayName = 'TransformNode';
