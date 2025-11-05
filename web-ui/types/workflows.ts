/**
 * Workflow Types and Interfaces
 */

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  triggers: WorkflowTrigger[];
  actions: WorkflowAction[];
  status: WorkflowStatus;
  created_at: string;
  updated_at: string;
  last_run?: string;
  run_count: number;
  success_count: number;
  error_count: number;
}

export type WorkflowStatus = 'active' | 'inactive' | 'running' | 'error' | 'paused';

export interface WorkflowTrigger {
  type: TriggerType;
  config: TriggerConfig;
}

export type TriggerType = 'schedule' | 'webhook' | 'event' | 'manual';

export interface TriggerConfig {
  schedule?: string; // Cron expression
  webhook_url?: string;
  event_type?: string;
  conditions?: Record<string, unknown>;
}

export interface WorkflowAction {
  type: ActionType;
  config: ActionConfig;
  order?: number;
}

export type ActionType =
  | 'send_email'
  | 'api_call'
  | 'database_query'
  | 'ai_task'
  | 'notification'
  | 'conditional';

export interface ActionConfig {
  name?: string;
  email_to?: string;
  email_subject?: string;
  email_body?: string;
  api_url?: string;
  api_method?: string;
  api_headers?: Record<string, string>;
  api_body?: Record<string, unknown>;
  query?: string;
  ai_prompt?: string;
  notification_channel?: string;
  condition?: string;
  [key: string]: unknown;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  result?: WorkflowResult;
  error?: string;
}

export interface WorkflowResult {
  success: boolean;
  duration_ms: number;
  outputs: Record<string, unknown>;
  logs?: string[];
}