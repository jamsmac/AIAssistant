import { create } from "zustand";
import { nanoid } from "nanoid";
import type {
  Edge,
  Node,
  OnConnect,
  OnEdgesChange,
  OnNodesChange,
  ReactFlowInstance,
} from "reactflow";
import { addEdge, applyEdgeChanges, applyNodeChanges } from "reactflow";

export type WorkflowNodeType = "trigger" | "action" | "condition" | "loop" | "transform";

export interface WorkflowNodeData {
  label: string;
  description?: string;
  config: Record<string, unknown>;
  errors?: string[];
}

export interface WorkflowStateNode extends Node<WorkflowNodeData> {
  type: WorkflowNodeType;
}

export interface WorkflowValidationError {
  message: string;
  nodeId?: string;
}

export interface WorkflowBuildResult {
  trigger?: {
    type: string;
    config: Record<string, unknown>;
  };
  actions: Array<{
    type: string;
    config: Record<string, unknown>;
  }>;
  layout: {
    nodes: Array<{ id: string; type: WorkflowNodeType; position: { x: number; y: number }; data: WorkflowNodeData }>;
    edges: Array<{ id: string; source: string; target: string; label?: string }>;
  };
  errors: WorkflowValidationError[];
}

interface WorkflowState {
  nodes: WorkflowStateNode[];
  edges: Edge[];
  selectedNodeId: string | null;
  reactFlowInstance: ReactFlowInstance | null;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  addNode: (type: WorkflowNodeType, position?: { x: number; y: number }) => void;
  updateNodeData: (id: string, data: Partial<WorkflowNodeData>) => void;
  removeNode: (id: string) => void;
  setSelectedNode: (id: string | null) => void;
  setReactFlowInstance: (instance: ReactFlowInstance) => void;
  setNodeErrors: (id: string, errors: string[]) => void;
  clearNodeErrors: () => void;
  reset: () => void;
  resetAll: () => void;
  loadWorkflow: (workflow: any) => void;
  toWorkflow: () => WorkflowBuildResult;
}

const DEFAULT_NODE_DATA: Record<WorkflowNodeType, WorkflowNodeData> = {
  trigger: {
    label: "Trigger",
    description: "Define how this workflow starts",
    config: {
      triggerType: "manual",
    },
  },
  action: {
    label: "Action",
    description: "Perform an action when triggered",
    config: {
      actionType: "send_email",
      to: "",
      subject: "",
      body: "",
    },
  },
  condition: {
    label: "Condition",
    description: "Branch the workflow based on an expression",
    config: {
      expression: "",
    },
  },
  loop: {
    label: "Loop",
    description: "Repeat a set of actions",
    config: {
      iterations: 3,
      variable: "item",
    },
  },
  transform: {
    label: "Transform",
    description: "Modify data with custom logic",
    config: {
      script: "// return transformed data\nreturn input;",
    },
  },
};

function cloneNodeData(type: WorkflowNodeType): WorkflowNodeData {
  const template = DEFAULT_NODE_DATA[type];
  return {
    label: template.label,
    description: template.description,
    config: JSON.parse(JSON.stringify(template.config ?? {})),
    errors: [],
  };
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  reactFlowInstance: null,
  onNodesChange: changes =>
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    }),
  onEdgesChange: changes =>
    set({
      edges: applyEdgeChanges(changes, get().edges),
    }),
  onConnect: connection =>
    set({
      edges: addEdge({ ...connection, animated: true, type: "smoothstep" }, get().edges),
    }),
  addNode: (type, position) =>
    set(state => {
      const id = nanoid(7);
      const nodePosition = position ?? { x: 200 + state.nodes.length * 40, y: 120 + state.nodes.length * 40 };
      return {
        nodes: [
          ...state.nodes,
          {
            id,
            type,
            position: nodePosition,
            data: cloneNodeData(type),
          },
        ],
        selectedNodeId: id,
      };
    }),
  updateNodeData: (id, data) =>
    set(state => ({
      nodes: state.nodes.map(node =>
        node.id === id
          ? {
              ...node,
              data: {
                ...node.data,
                ...data,
                config: {
                  ...node.data.config,
                  ...(data.config ?? {}),
                },
              },
            }
          : node,
      ),
    })),
  removeNode: id =>
    set(state => ({
      nodes: state.nodes.filter(node => node.id !== id),
      edges: state.edges.filter(edge => edge.source !== id && edge.target !== id),
      selectedNodeId: state.selectedNodeId === id ? null : state.selectedNodeId,
    })),
  setSelectedNode: id => set({ selectedNodeId: id }),
  setReactFlowInstance: instance => set({ reactFlowInstance: instance }),
  setNodeErrors: (id, errors) =>
    set(state => ({
      nodes: state.nodes.map(node =>
        node.id === id
          ? {
              ...node,
              data: {
                ...node.data,
                errors,
              },
            }
          : node,
      ),
    })),
  clearNodeErrors: () =>
    set(state => ({
      nodes: state.nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          errors: [],
        },
      })),
    })),
  reset: () => set({ nodes: [], edges: [], selectedNodeId: null }),
  resetAll: () => set({ nodes: [], edges: [], selectedNodeId: null, reactFlowInstance: null }),
  loadWorkflow: workflow => {
    if (!workflow) return;
    const nodes = (workflow.nodes ?? []).map((node: any) => ({
      id: node.id ?? nanoid(7),
      type: (node.type as WorkflowNodeType) ?? "action",
      position: node.position ?? { x: 0, y: 0 },
      data: {
        label: node.data?.label ?? cloneNodeData(node.type ?? "action").label,
        description: node.data?.description ?? "",
        config: node.data?.config ?? {},
        errors: [],
      },
    }));
    const edges = (workflow.edges ?? []).map((edge: any, index: number) => ({
      id: edge.id ?? `e-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: "smoothstep",
    }));
    set({ nodes, edges, selectedNodeId: nodes.length ? nodes[0].id : null });
  },
  toWorkflow: () => {
    const state = get();
    const nodes = state.nodes;
    const edges = state.edges;
    const errors: WorkflowValidationError[] = [];
    const nodeErrors: Record<string, string[]> = {};

    const pushNodeError = (nodeId: string, message: string) => {
      nodeErrors[nodeId] = [...(nodeErrors[nodeId] ?? []), message];
      errors.push({ nodeId, message });
    };

    state.clearNodeErrors();

    const triggerNodes = nodes.filter(node => node.type === "trigger");
    if (triggerNodes.length === 0) {
      errors.push({ message: "Add at least one trigger node" });
    }
    if (triggerNodes.length > 1) {
      triggerNodes.forEach(node => pushNodeError(node.id, "Only one trigger is allowed"));
    }

    const triggerNode = triggerNodes[0];
    let trigger;
    if (triggerNode) {
      const triggerConfig = triggerNode.data.config ?? {};
      const triggerType = String((triggerConfig as any).triggerType ?? "manual");
      if (triggerType === "schedule" && !(triggerConfig as any).cron) {
        pushNodeError(triggerNode.id, "Schedule trigger requires a cron expression");
      }
      const { triggerType: _, ...restConfig } = triggerConfig as Record<string, unknown>;
      trigger = {
        type: triggerType,
        config: restConfig,
      };
    }

    const adjacency: Record<string, string[]> = {};
    edges.forEach(edge => {
      adjacency[edge.source] = adjacency[edge.source] ?? [];
      adjacency[edge.source].push(edge.target);
    });

    const visited = new Set<string>();
    const traversalQueue: string[] = triggerNode ? [triggerNode.id] : [];
    const orderedNodes: WorkflowStateNode[] = [];

    while (traversalQueue.length) {
      const currentId = traversalQueue.shift()!;
      if (visited.has(currentId)) continue;
      visited.add(currentId);
      const node = nodes.find(n => n.id === currentId);
      if (node && (!triggerNode || node.id !== triggerNode.id)) {
        orderedNodes.push(node);
      }
      (adjacency[currentId] ?? []).forEach(targetId => traversalQueue.push(targetId));
    }

    nodes
      .filter(node => !visited.has(node.id) && node.type !== "trigger")
      .forEach(node => pushNodeError(node.id, "Node is not connected to the trigger"));

    const actions: Array<{ type: string; config: Record<string, unknown> }> = [];
    orderedNodes.forEach(node => {
      const config = node.data.config ?? {};
      switch (node.type) {
        case "action": {
          const actionType = String((config as any).actionType ?? "");
          if (!actionType) {
            pushNodeError(node.id, "Select an action type");
          }
          const { actionType: _, ...rest } = config as Record<string, unknown>;
          actions.push({ type: actionType || "custom", config: rest });
          break;
        }
        case "condition": {
          if (!(config as any).expression) {
            pushNodeError(node.id, "Condition requires an expression");
          }
          actions.push({ type: "condition", config });
          break;
        }
        case "loop": {
          if (!(config as any).iterations) {
            pushNodeError(node.id, "Loop requires iterations count");
          }
          actions.push({ type: "loop", config });
          break;
        }
        case "transform": {
          if (!(config as any).script) {
            pushNodeError(node.id, "Transform requires a script");
          }
          actions.push({ type: "transform", config });
          break;
        }
        default:
          break;
      }
    });

    Object.keys(nodeErrors).forEach(nodeId => {
      get().setNodeErrors(nodeId, nodeErrors[nodeId]);
    });
    nodes
      .filter(node => !nodeErrors[node.id])
      .forEach(node => get().setNodeErrors(node.id, []));

    return {
      trigger,
      actions,
      layout: {
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          position: node.position,
          data: {
            label: node.data.label,
            description: node.data.description,
            config: node.data.config,
            errors: node.data.errors ?? [],
          },
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.label,
        })),
      },
      errors,
    };
  },
}));
