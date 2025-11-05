/**
 * Database and Schema Types
 */

export interface Database {
  id: string;
  project_id: string;
  name: string;
  type: DatabaseType;
  description?: string;
  connection_string?: string;
  tables: DatabaseTable[];
  created_at: string;
  updated_at: string;
}

export type DatabaseType = 'postgresql' | 'mysql' | 'sqlite' | 'mongodb' | 'redis';

export interface DatabaseTable {
  id: string;
  name: string;
  columns: TableColumn[];
  row_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TableColumn {
  name: string;
  type: ColumnType;
  primary_key?: boolean;
  nullable?: boolean;
  unique?: boolean;
  default_value?: string | number | boolean | null;
  references?: {
    table: string;
    column: string;
  };
}

export type ColumnType =
  | 'uuid'
  | 'varchar'
  | 'text'
  | 'int'
  | 'bigint'
  | 'float'
  | 'double'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'timestamp'
  | 'json'
  | 'jsonb';

export interface TableRow {
  id: string | number;
  data: Record<string, ColumnValue>;
  created_at?: string;
  updated_at?: string;
}

export type ColumnValue = string | number | boolean | null | Date | Record<string, unknown>;

export interface QueryResult {
  rows: TableRow[];
  fields: string[];
  row_count: number;
  execution_time_ms?: number;
}

export interface SchemaUpdate {
  table: string;
  operation: 'create' | 'alter' | 'drop';
  changes: {
    columns?: TableColumn[];
    add_columns?: TableColumn[];
    drop_columns?: string[];
    rename_columns?: Array<{ from: string; to: string }>;
  };
}