// API service for frontend

import axios from 'axios';

import type {
  DatasetInfo,
  DatasetProfile,
  ValidationReport,
  ChatResponse,
  Session,
  AnomalyResult,
  ExportResult,
} from '../types';

export interface UploadResponse {
  success?: boolean;
  uploaded?: Array<
    DatasetInfo & {
      filename?: string;
      quality_score?: number;
    }
  >;
  errors?: Array<{
    filename?: string;
    error?: string;
    details?: unknown;
  }>;
  total_uploaded?: number;
  total_failed?: number;
}

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Datasets
export const datasetsApi = {
  list: () =>
    api.get<{ datasets: DatasetInfo[]; count: number }>('/datasets'),

  get: (id: string) =>
    api.get<DatasetInfo>(`/datasets/${id}`),

  profile: (id: string) =>
    api.get<DatasetProfile>(`/datasets/${id}/profile`),

  quality: (id: string) =>
    api.get<ValidationReport>(`/datasets/${id}/quality`),

  preview: (id: string, nrows?: number) =>
    api.get(`/datasets/${id}/preview`, {
      params: { nrows },
    }),

  schema: (id: string) =>
    api.get(`/datasets/${id}/schema`),

  delete: (id: string) =>
    api.delete(`/datasets/${id}`),

  allSchemas: () =>
    api.get('/schema'),
};

// Upload
export const uploadApi = {
  upload: (files: File[], datasetIds?: string[]) => {
    const formData = new FormData();

    files.forEach((f) => formData.append('files', f));

    if (datasetIds) {
      datasetIds.forEach((id) =>
        formData.append('dataset_ids', id)
      );
    }

    return api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  preview: (file: File, nrows?: number) => {
    const formData = new FormData();

    formData.append('file', file);

    return api.post('/upload/preview', formData, {
      params: { nrows },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Chat
export const chatApi = {
  send: (
    datasetId: string,
    message: string,
    sessionId?: string
  ) =>
    api.post<ChatResponse>('/chat', {
      dataset_id: datasetId,
      message,
      session_id: sessionId,
    }),

  createSession: (datasetId?: string) =>
    api.post<{
      session_id: string;
      dataset_id: string;
    }>('/sessions', {
      dataset_id: datasetId,
    }),

  listSessions: (datasetId?: string) =>
    api.get<{
      sessions: Session[];
      count: number;
    }>('/sessions', {
      params: {
        dataset_id: datasetId,
      },
    }),

  getSession: (sessionId: string) =>
    api.get<Session>(`/sessions/${sessionId}`),

  getHistory: (sessionId: string, limit?: number) =>
    api.get(`/sessions/${sessionId}/history`, {
      params: { limit },
    }),

  deleteSession: (sessionId: string) =>
    api.delete(`/sessions/${sessionId}`),
};

// Anomalies
export const anomaliesApi = {
  detect: (
    datasetId: string,
    column: string,
    method: string,
    threshold?: number
  ) =>
    api.post('/anomalies/detect', {
      dataset_id: datasetId,
      column,
      method,
      threshold,
    }),

  detectMultivariate: (
    datasetId: string,
    columns: string[],
    contamination?: number
  ) =>
    api.post('/anomalies/detect-multivariate', {
      dataset_id: datasetId,
      columns,
      contamination,
    }),

  methods: () =>
    api.get('/anomalies/methods'),
};

// Charts
export const chartsApi = {
  generate: (
    datasetId: string,
    chartType: string,
    xColumn: string,
    yColumn?: string,
    colorColumn?: string,
    title?: string
  ) =>
    api.post('/charts/generate', {
      dataset_id: datasetId,
      chart_type: chartType,
      x_column: xColumn,
      y_column: yColumn,
      color_column: colorColumn,
      title,
    }),

  auto: (
    datasetId: string,
    xColumn: string,
    yColumn?: string
  ) =>
    api.post('/charts/auto', {
      dataset_id: datasetId,
      x_column: xColumn,
      y_column: yColumn,
    }),

  types: () =>
    api.get('/charts/types'),
};

// Quality
export const qualityApi = {
  check: (datasetId: string) =>
    api.get(`/quality/${datasetId}`),

  summary: (datasetId: string) =>
    api.get(`/quality/${datasetId}/summary`),
};

// Export
export const exportApi = {
  data: (
    datasetId: string,
    format: string,
    filename?: string
  ) =>
    api.post('/export/data', {
      dataset_id: datasetId,
      format,
      filename,
    }),

  chart: (
    chartJson: any,
    format: string,
    filename?: string
  ) =>
    api.post('/export/chart', {
      chart_json: chartJson,
      format,
      filename,
    }),

  report: (
    sessionId: string,
    format: string,
    filename?: string
  ) =>
    api.post('/export/report', {
      session_id: sessionId,
      format,
      filename,
    }),

  formats: () =>
    api.get('/export/formats'),
};

export default api;