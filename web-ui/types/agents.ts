/**
 * Agent Types and Interfaces
 */

export interface Agent {
  id: string;
  organization_id: string;
  name: string;
  type: AgentType;
  description?: string;
  status: AgentStatus;
  capabilities: string[];
  config: AgentConfig;
  parent_agent_id?: string;
  depth_level: number;
  hierarchy_path: string;
  created_at: string;
  updated_at: string;
  last_active_at?: string;
  task_count?: number;
  success_rate?: number;
}

export type AgentType = 'coordinator' | 'specialist' | 'worker' | 'analyst' | 'reviewer';

export type AgentStatus = 'active' | 'idle' | 'busy' | 'error' | 'offline';

export interface AgentConfig {
  model?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: string[];
  memory_enabled?: boolean;
  auto_decompose?: boolean;
  max_subtasks?: number;
  [key: string]: unknown;
}

export interface AgentNodeData {
  id: string;
  label: string;
  type: AgentType;
  status: AgentStatus;
  capabilities: string[];
  taskCount: number;
  successRate: number;
}

export interface AgentConnector {
  id: string;
  source_agent_id: string;
  target_agent_id: string;
  connector_type: ConnectorType;
  weight: number;
  is_active: boolean;
  created_at: string;
}

export type ConnectorType = 'delegation' | 'collaboration' | 'consultation' | 'supervision';

export interface AgentMetrics {
  agent_id: string;
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  average_completion_time: number;
  success_rate: number;
  last_updated: string;
}