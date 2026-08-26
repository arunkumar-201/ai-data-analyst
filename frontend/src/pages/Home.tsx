import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { datasetsApi, uploadApi } from '../services/api';
import type { DatasetInfo } from '../types';
import { UploadZone } from '../components/UploadZone';
import { DatasetCard } from '../components/DatasetCard';
import {
  Database,
  BarChart2,
  MessageSquare,
  AlertTriangle,
  ArrowRight,
  Plus,
  Search,
  FileText,
} from 'lucide-react';
import { clsx } from 'clsx';

export function Home() {
  const navigate = useNavigate();
  const { datasets, setDatasets, currentDatasetId, setCurrentDataset, setIsUploading } = useAppStore();
  const [stats, setStats] = useState({
    totalDatasets: 0,
    totalRows: 0,
    totalColumns: 0,
    totalSize: 0,
  });

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await datasetsApi.list();
      const datasetList = response.data.datasets || [];
      setDatasets(datasetList);

      const totalRows = datasetList.reduce((sum, d) => sum + d.rows, 0);
      const totalColumns = datasetList.reduce((sum, d) => sum + d.columns, 0);
      const totalSize = datasetList.reduce((sum, d) => sum + d.file_size_mb, 0);

      setStats({
        totalDatasets: datasetList.length,
        totalRows,
        totalColumns,
        totalSize,
      });
    } catch (error) {
      console.error('Failed to load datasets:', error);
    }
  };

  const handleUploadComplete = (datasetIds: string[]) => {
    loadDatasets();
    if (datasetIds.length > 0) {
      setCurrentDataset(datasetIds[0]);
      navigate('/chat');
    }
  };

  const handlePreview = async (file: File) => {
    try {
      setIsUploading(true);
      await uploadApi.preview(file);
    } catch (error) {
      console.error('Preview failed:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const quickActions = [
    { name: 'Chat with Data', icon: MessageSquare, href: '/chat', desc: 'Ask questions in natural language' },
    { name: 'Data Quality', icon: AlertTriangle, href: '/quality', desc: 'Validate and profile your data' },
    { name: 'Anomaly Detection', icon: Search, href: '/anomalies', desc: 'Find outliers and anomalies' },
    { name: 'Generate Reports', icon: FileText, href: '/reports', desc: 'Create and export analysis reports' },
  ];

  if (datasets.length === 0) {
    return (
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="text-center py-12">
          <div className="w-20 h-20 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <BarChart2 className="w-10 h-10 text-primary-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to AI Data Analyst</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload CSV files to start analyzing your data with natural language queries,
            automatic visualizations, anomaly detection, and comprehensive data quality reports.
          </p>
        </div>

        {/* Upload Zone */}
        <UploadZone onUploadComplete={handleUploadComplete} />

        {/* Quick Actions */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map(action => (
              <button
                key={action.name}
                onClick={() => navigate(action.href)}
                disabled={!currentDatasetId && action.href !== '/chat'}
                className={clsx(
                  'card p-6 text-left group transition-all hover:shadow-md hover:border-primary-300',
                  !currentDatasetId && action.href !== '/chat' && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-primary-200 transition-colors">
                  <action.icon className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{action.name}</h3>
                <p className="text-sm text-gray-500">{action.desc}</p>
                <div className="mt-4 flex items-center justify-end">
                  <ArrowRight className={clsx('w-4 h-4 text-gray-400 group-hover:text-primary-600 transition-colors', !currentDatasetId && action.href !== '/chat' && 'opacity-0')} />
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Datasets</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalDatasets}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Rows</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalRows.toLocaleString()}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Columns</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalColumns.toLocaleString()}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <BarChart2 className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Total Size</p>
              <p className="text-3xl font-bold text-gray-900">{stats.totalSize.toFixed(1)} MB</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <UploadZone onUploadComplete={handleUploadComplete} />

      {/* Recent Datasets */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Recent Datasets</h2>
        <button
          onClick={() => navigate('/datasets')}
          className="btn-secondary text-sm flex items-center gap-1"
        >
          View All
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {datasets.slice(0, 6).map(dataset => (
          <DatasetCard key={dataset.dataset_id} dataset={dataset} />
        ))}
      </div>

      {datasets.length > 6 && (
        <div className="text-center">
          <button
            onClick={() => navigate('/datasets')}
            className="btn-secondary"
          >
            View all {datasets.length} datasets
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>
        </div>
      )}
    </div>
  );
}