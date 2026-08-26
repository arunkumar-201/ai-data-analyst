import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { datasetsApi, qualityApi } from '../services/api';
import type { DatasetInfo, ValidationReport, DatasetProfile } from '../types';
import { QualityDashboard } from '../components/QualityDashboard';
import { DatasetCard } from '../components/DatasetCard';
import {
  AlertTriangle,
  Database,
  ChevronDown,
  Download,
  RefreshCw,
  FileText,
  BarChart2,
  Eye,
} from 'lucide-react';
import { clsx } from 'clsx';

export function Quality() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { datasets, currentDatasetId, setCurrentDataset, setDatasets } = useAppStore();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(currentDatasetId || searchParams.get('dataset') || '');
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDatasetPicker, setShowDatasetPicker] = useState(false);
  const [activeTab, setActiveTab] = useState<'quality' | 'profile'>('quality');

  const handleExport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `quality-report-${selectedDatasetId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (datasets.length === 0) {
      loadDatasets();
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      loadQualityData(selectedDatasetId);
    }
  }, [selectedDatasetId]);

  useEffect(() => {
    if (searchParams.get('tab') === 'profile') {
      setActiveTab('profile');
    }
  }, [searchParams]);

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

  const loadQualityData = async (datasetId: string) => {
    setIsLoading(true);
    try {
      const [qualityRes, profileRes] = await Promise.all([
        qualityApi.check(datasetId),
        datasetsApi.profile(datasetId),
      ]);
      setReport(qualityRes.data);
      setProfile(profileRes.data);
    } catch (error) {
      console.error('Failed to load quality data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (selectedDatasetId) {
      await loadQualityData(selectedDatasetId);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString([], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`;
    return `${mb.toFixed(2)} MB`;
  };

  if (!selectedDatasetId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Quality</h1>
          <p className="text-gray-500 mt-1">Validate and profile your datasets</p>
        </div>

        <div className="card p-12 text-center">
          <AlertTriangle className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">Select a Dataset</h3>
          <p className="text-gray-500 mb-6">Choose a dataset from the sidebar or browse all datasets</p>
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

  const currentDataset = datasets.find(d => d.dataset_id === selectedDatasetId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Data Quality</h1>
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

          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-4" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('quality')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'quality'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <AlertTriangle className="w-4 h-4 inline mr-1" />
              Quality Issues
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'profile'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <BarChart2 className="w-4 h-4 inline mr-1" />
              Data Profile
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'quality' ? (
            <QualityDashboard
              report={report || { dataset_id: selectedDatasetId, rows: 0, columns: 0, issues: [], quality_score: 0 }}
              onExport={handleExport}
            />
          ) : (
            <DataProfileView profile={profile} dataset={currentDataset} />
          )}
        </div>
      </div>
    </div>
  );
}

function DataProfileView({ profile, dataset }: { profile: DatasetProfile | null; dataset: DatasetInfo | undefined }) {
  if (!profile) {
    return (
      <div className="text-center py-12 text-gray-500">
        <BarChart2 className="w-12 h-12 mx-auto text-gray-300 mb-2" />
        <p>No profile data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Rows" value={profile.rows.toLocaleString()} icon={FileText} color="blue" />
        <StatCard label="Columns" value={profile.columns} icon={Database} color="green" />
        <StatCard label="Missing Values" value={profile.missing_values.toLocaleString()} icon={AlertTriangle} color="red" />
        <StatCard label="Duplicate Rows" value={profile.duplicate_rows.toLocaleString()} icon={AlertTriangle} color="yellow" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Numeric" value={profile.numeric_columns} icon={BarChart2} color="purple" />
        <StatCard label="Categorical" value={profile.categorical_columns} icon={Database} color="orange" />
        <StatCard label="Datetime" value={profile.datetime_columns} icon={BarChart2} color="cyan" />
        <StatCard label="Memory" value={`${profile.memory_usage_mb.toFixed(1)} MB`} icon={Database} color="gray" />
      </div>

      {/* Column Profiles */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Column Profiles</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Column</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Inferred</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Missing</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Unique</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Mean</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Std</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Min</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Max</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {profile.column_profiles.map((col, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{col.name}</td>
                  <td className="px-4 py-3 text-gray-600">{col.dtype}</td>
                  <td className="px-4 py-3 text-gray-600">{col.inferred_type}</td>
                  <td className="px-4 py-3 text-gray-600">{col.missing_count} ({col.missing_percentage.toFixed(1)}%)</td>
                  <td className="px-4 py-3 text-gray-600">{col.unique_count}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono">{col.mean?.toFixed(2) || 'N/A'}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono">{col.std?.toFixed(2) || 'N/A'}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono">{col.min?.toFixed(2) || 'N/A'}</td>
                  <td className="px-4 py-3 text-gray-600 font-mono">{col.max?.toFixed(2) || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: React.ComponentType<{ className?: string }>; color: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
    cyan: 'bg-cyan-100 text-cyan-600',
    gray: 'bg-gray-100 text-gray-600',
  };

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', colorMap[color])}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}