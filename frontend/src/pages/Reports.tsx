import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { chatApi, datasetsApi, exportApi } from '../services/api';
import type { Session, DatasetInfo } from '../types';
import { DatasetCard } from '../components/DatasetCard';
import {
  FileText,
  Database,
  ChevronDown,
  Download,
  RefreshCw,
  Eye,
  Trash2,
  Share2,
  FilePlus,
  BarChart2,
  AlertTriangle,
  MessageSquare,
  Check,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';

export function Reports() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { datasets, sessions, currentDatasetId, setCurrentDataset, setDatasets, setSessions } = useAppStore();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(searchParams.get('dataset') || currentDatasetId || '');
  const [showDatasetPicker, setShowDatasetPicker] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportFormat, setReportFormat] = useState<'html' | 'pdf' | 'json'>('html');
  const [generatedReport, setGeneratedReport] = useState<string | null>(null);

  useEffect(() => {
    if (datasets.length === 0) {
      loadDatasets();
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      loadSessions(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  const loadDatasets = async () => {
    try {
      const response = await datasetsApi.list();
      setDatasets(response.data.datasets || []);
      if (!selectedDatasetId && response.data.datasets.length > 0) {
        const firstId = response.data.datasets[0].dataset_id;
        setSelectedDatasetId(firstId);
        setCurrentDataset(firstId);
      }
    } catch (error) {
      console.error('Failed to load datasets:', error);
    }
  };

  const loadSessions = async (datasetId: string) => {
    try {
      const response = await chatApi.listSessions(datasetId);
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedSessionId) return;
    setIsGenerating(true);
    try {
      const response = await exportApi.report(selectedSessionId, reportFormat);
      const downloadUrl = response.data.download_url;
      // Trigger download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = response.data.filename || `report.${reportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error('Report generation failed:', error);
      alert('Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportData = async (format: 'csv' | 'excel' | 'json') => {
    if (!selectedDatasetId) return;
    try {
      const response = await exportApi.data(selectedDatasetId, format);
      const a = document.createElement('a');
      a.href = response.data.download_url;
      a.download = response.data.filename || `data.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export data');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = diff / (1000 * 60 * 60);
    const days = diff / (1000 * 60 * 60 * 24);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    if (days < 7) return `${Math.floor(days)}d ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const getSessionPreview = (session: Session) => {
    const lastMessage = session.messages[session.messages.length - 1];
    if (lastMessage) {
      return lastMessage.content.slice(0, 60) + (lastMessage.content.length > 60 ? '...' : '');
    }
    return 'New conversation';
  };

  const currentDataset = datasets.find(d => d.dataset_id === selectedDatasetId);
  const currentSession = sessions.find(s => s.session_id === selectedSessionId);

  if (!selectedDatasetId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports & Exports</h1>
          <p className="text-gray-500 mt-1">Generate reports and export data</p>
        </div>

        <div className="card p-12 text-center">
          <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">Select a Dataset</h3>
          <p className="text-gray-500 mb-6">Choose a dataset to generate reports from chat sessions</p>
          <button
            onClick={() => setShowDatasetPicker(true)}
            className="btn-primary"
          >
            Browse Datasets
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
            <FileText className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reports & Exports</h1>
            <p className="text-gray-500 mt-1">
              {currentDataset?.original_filename || 'No dataset selected'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Dataset Picker */}
          <div className="relative">
            <button
              onClick={() => setShowDatasetPicker(!showDatasetPicker)}
              className="btn-secondary flex items-center gap-2"
            >
              <Database className="w-4 h-4" />
              <span className="hidden sm:inline">{currentDataset?.original_filename || 'Select Dataset'}</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {showDatasetPicker && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowDatasetPicker(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 w-72 bg-white rounded-lg shadow-lg border border-gray-200 py-1 max-h-60 overflow-y-auto">
                  {datasets.map(dataset => (
                    <button
                      key={dataset.dataset_id}
                      onClick={() => {
                        setSelectedDatasetId(dataset.dataset_id);
                        setCurrentDataset(dataset.dataset_id);
                        setShowDatasetPicker(false);
                      }}
                      className={clsx('w-full px-4 py-2 text-left text-sm', selectedDatasetId === dataset.dataset_id ? 'bg-primary-50 text-primary-700' : 'text-gray-700 hover:bg-gray-50')}
                    >
                      {dataset.original_filename}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Data Export Section */}
      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Data Export
          </h3>
        </div>
        <div className="p-4">
          <p className="text-gray-600 mb-4">Export the raw dataset in various formats</p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleExportData('csv')}
              className="btn-secondary flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Export as CSV
            </button>
            <button
              onClick={() => handleExportData('excel')}
              className="btn-secondary flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Export as Excel
            </button>
            <button
              onClick={() => handleExportData('json')}
              className="btn-secondary flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Export as JSON
            </button>
          </div>
        </div>
      </div>

      {/* Chat Session Reports */}
      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-green-600" />
            Session Reports
          </h3>
        </div>
        <div className="p-4">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="w-12 h-12 mx-auto text-gray-300 mb-2" />
              <p>No chat sessions for this dataset</p>
              <p className="text-sm mt-1">Start a conversation in the Chat page to generate reports</p>
              <button
                onClick={() => navigate('/chat')}
                className="btn-primary mt-4"
              >
                Go to Chat
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-4">
                <label className="text-sm font-medium text-gray-700">Format:</label>
                <div className="flex items-center gap-2 border border-gray-200 rounded-lg overflow-hidden">
                  {(['html', 'pdf', 'json'] as const).map(fmt => (
                    <button
                      key={fmt}
                      onClick={() => setReportFormat(fmt)}
                      className={clsx(
                        'px-4 py-2 text-sm font-medium transition-colors',
                        reportFormat === fmt
                          ? 'bg-primary-600 text-white'
                          : 'text-gray-700 hover:bg-gray-50'
                      )}
                    >
                      {fmt.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {sessions.map(session => (
                  <div
                    key={session.session_id}
                    className={clsx(
                      'p-4 rounded-lg border transition-colors',
                      selectedSessionId === session.session_id
                        ? 'bg-primary-50 border-primary-300'
                        : 'border-gray-200 hover:border-gray-300'
                    )}
                    onClick={() => setSelectedSessionId(session.session_id)}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{getSessionPreview(session)}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                          <span>{formatDate(session.updated_at)}</span>
                          <span>{session.messages.length} messages</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {selectedSessionId === session.session_id && (
                          <div className="w-5 h-5 rounded-full bg-primary-600 flex items-center justify-center">
                            <Check className="w-3 h-3 text-white" />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {selectedSessionId && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={handleGenerateReport}
                    disabled={isGenerating}
                    className="btn-primary w-full flex items-center justify-center gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4" />
                        Generate {reportFormat.toUpperCase()} Report
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-600" />
            Quick Actions
          </h3>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/chat')}
            className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-gray-50 transition-colors text-left group"
          >
            <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-green-200 transition-colors">
              <MessageSquare className="w-5 h-5 text-green-600" />
            </div>
            <h4 className="font-medium text-gray-900">Chat Analysis</h4>
            <p className="text-sm text-gray-500 mt-1">Ask questions about your data</p>
          </button>

          <button
            onClick={() => navigate(`/quality?dataset=${selectedDatasetId}`)}
            className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-gray-50 transition-colors text-left group"
          >
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-red-200 transition-colors">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <h4 className="font-medium text-gray-900">Data Quality</h4>
            <p className="text-sm text-gray-500 mt-1">Validate and profile your data</p>
          </button>

          <button
            onClick={() => navigate(`/anomalies?dataset=${selectedDatasetId}`)}
            className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-gray-50 transition-colors text-left group"
          >
            <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-yellow-200 transition-colors">
              <Zap className="w-5 h-5 text-yellow-600" />
            </div>
            <h4 className="font-medium text-gray-900">Anomaly Detection</h4>
            <p className="text-sm text-gray-500 mt-1">Find outliers in your data</p>
          </button>

          <button
            onClick={() => navigate('/datasets')}
            className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-gray-50 transition-colors text-left group"
          >
            <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center mb-3 group-hover:bg-blue-200 transition-colors">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <h4 className="font-medium text-gray-900">Manage Datasets</h4>
            <p className="text-sm text-gray-500 mt-1">Upload, view, or delete datasets</p>
          </button>
        </div>
      </div>
    </div>
  );
}