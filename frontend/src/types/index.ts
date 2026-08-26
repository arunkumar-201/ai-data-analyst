// Type definitions for the frontend

export interface DatasetInfo {
  dataset_id: string;
  original_filename: string;
  rows: number;
  columns: number;
  profile?: DatasetProfile;
  validation_report?: ValidationReport;
  table_name: string;
  created_at: string;
  file_size_mb: number;
  source_path?: string;
}

export interface DatasetProfile {
  dataset_id: string;
  rows: number;
  columns: number;
  missing_values: number;
  missing_percentage: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  numeric_columns: number;
  categorical_columns: number;
  datetime_columns: number;
  boolean_columns: number;
  text_columns: number;
  column_profiles: ColumnProfile[];
  memory_usage_mb: number;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  inferred_type: string;
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  cardinality: number;
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  q1?: number;
  q3?: number;
  iqr?: number;
  skewness?: number;
  kurtosis?: number;
  top_values?: Array<{
    value: string;
    count: number;
  }>;
  value_counts?: Record<string, number>;
  min_date?: string;
  max_date?: string;
  date_range_days?: number;
  histogram?: {
    bins: number[];
    counts: number[];
  };
}

export interface ValidationReport {
  dataset_id: string;
  rows: number;
  columns: number;
  issues: ValidationIssue[];
  quality_score: number;
}

export interface ValidationIssue {
  column: string;
  issue: string;
  count: number;
  percentage: number;
  severity: 'high' | 'medium' | 'low' | 'info';
  recommendation: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;

  metadata?: {
    sql?: string;
    pandas_code?: string;
    chart_type?: string;
    chart?: ChartResult;
    intent?: string;
    trace?: TraceStep[];

    // IMPORTANT:
    // Store backend query results here so the frontend
    // can display them even when the trace only contains
    // row counts.
    results?: ToolResult[];
  };
}

export interface TraceStep {
  step: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface ChatResponse {
  success: boolean;
  session_id: string;
  answer: string;
  explanation?: string;
  sql?: string;
  pandas_code?: string;
  chart?: ChartResult;
  trace: TraceStep[];

  // Actual tool results returned by the backend
  results: ToolResult[];

  error?: string;
}

export interface ChartResult {
  success: boolean;
  chart_json?: string;
  chart_type: string;
  title: string;
  error?: string;
}

export interface ToolResult {
  success: boolean;

  // Actual rows returned by SQL/Pandas
  data?: any[];

  // Column names returned by SQL/Pandas
  columns?: string[];

  // Number of rows
  row_count?: number;

  execution_time_ms?: number;

  sql?: string;

  code?: string;

  error?: string;

  anomalies?: AnomalyResult[];

  explanation?: string;

  statistics?: Record<string, any>;
}

export interface AnomalyResult {
  index: number;
  column: string;
  value: number;
  z_score?: number;
  lower_bound?: number;
  upper_bound?: number;
  direction?: string;
  deviation_iqr?: number;
  anomaly_score?: number;
  normalized_score?: number;
  severity: 'high' | 'medium' | 'low';
  reason: string;
}

export interface Session {
  session_id: string;
  dataset_id?: string;
  messages: ChatMessage[];
  context: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ExportResult {
  format: string;
  file_path: string;
  file_size: number;
  download_url: string;
}
