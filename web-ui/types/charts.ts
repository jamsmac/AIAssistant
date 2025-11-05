/**
 * Chart and Analytics Types
 */

export interface ChartDataPoint {
  name: string;
  value: number;
  percent?: number;
  label?: string;
  color?: string;
}

export interface TimeSeriesData {
  timestamp: string | Date;
  value: number;
  category?: string;
}

export interface PieChartData extends ChartDataPoint {
  percent: number;
}

export interface BarChartData {
  category: string;
  [key: string]: string | number;
}

export interface LineChartData {
  x: string | number | Date;
  y: number;
  series?: string;
}

export interface HeatmapData {
  x: string | number;
  y: string | number;
  value: number;
}

export interface TreemapData {
  name: string;
  size: number;
  children?: TreemapData[];
}

export interface SankeyNode {
  id: string;
  label: string;
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
}