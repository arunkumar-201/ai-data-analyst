import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { datasetsApi, anomaliesApi } from '../services/api';
import type { DatasetInfo, AnomalyResult } from '../types';
import { AnomalyCard } from '../components/AnomalyCard';
import { DatasetCard } from '../components/DatasetCard';
import {
  AlertTriangle,
  Database,
  ChevronDown,
  Search,
  Download,
  RefreshCw,
  BarChart2,
  Eye,
  SlidersHorizontal,
  Zap,
} from 'lucide-react';

function clsx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

const univariateMethods = [
  { value: 'zscore', label: 'Z-Score', desc: 'Standard score method (threshold-based)' },
  { value: 'iqr', label: 'IQR', desc: 'Interquartile range method' },
  { value: 'isolation_forest', label: 'Isolation Forest', desc: 'ML-based anomaly detection' },
];

interface SchemaColumn {
  name: string;
  type: string;
}

export function Anomalies() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { datasets, currentDatasetId, setCurrentDataset, setDatasets } = useAppStore();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(currentDatasetId || searchParams.get('dataset') || '');
  const [anomalies, setAnomalies] = useState<AnomalyResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDatasetPicker, setShowDatasetPicker] = useState(false);
  const [activeTab, setActiveTab] = useState<'univariate' | 'multivariate'>('univariate');
  const [selectedColumn, setSelectedColumn] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('zscore');
  const [threshold, setThreshold] = useState(3);
  const [multivariateColumns, setMultivariateColumns] = useState<string[]>([]);
  const [contamination, setContamination] = useState(0.1);
  const [columns, setColumns] = useState<SchemaColumn[]>([]);

  useEffect(() => {
    if (datasets.length === 0) {
      loadDatasets();
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId) {
      loadColumns(selectedDatasetId);
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

  const loadColumns = async (datasetId: string) => {
    try {
      const response = await datasetsApi.schema(datasetId);
      const cols: SchemaColumn[] = response.data.columns || [];
      setColumns(cols);
      // Auto-select first numeric column
      const numericCol = cols.find((c) => isNumericType(c.type));
      if (numericCol && !selectedColumn) {
        setSelectedColumn(numericCol.name);
      }
    } catch (error) {
      console.error('Failed to load columns:', error);
    }
  };

  const handleDetectUnivariate = async () => {
    if (!selectedDatasetId || !selectedColumn) return;
    setIsLoading(true);
    try {
      const response = await anomaliesApi.detect(selectedDatasetId, selectedColumn, selectedMethod, threshold);
      setAnomalies(response.data.anomalies || []);
    } catch (error) {
      console.error('Anomaly detection failed:', error);
      alert('Anomaly detection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDetectMultivariate = async () => {
    if (!selectedDatasetId || multivariateColumns.length === 0) return;
    setIsLoading(true);
    try {
      const response = await anomaliesApi.detectMultivariate(selectedDatasetId, multivariateColumns, contamination);
      setAnomalies(response.data.anomalies || []);
    } catch (error) {
      console.error('Multivariate detection failed:', error);
      alert('Multivariate detection failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (anomalies.length === 0) return;
    const blob = new Blob([JSON.stringify({ dataset_id: selectedDatasetId, anomalies }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `anomalies-${selectedDatasetId}.json`;
    link.click();
    URL.revokeObjectURL(url);
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

  if (!selectedDatasetId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Anomaly Detection</h1>
          <p className="text-gray-500 mt-1">Find outliers and anomalies in your data</p>
        </div>

        <div className="card p-12 text-center">
          <Zap className="w-16 h-16 mx-auto text-gray-300 mb-4" />
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
  const numericColumns = columns.filter(c => isNumericType(c.type)).map(c => c.name);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
            <Zap className="w-6 h-6 text-yellow-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Anomaly Detection</h1>
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

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-4" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('univariate')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'univariate'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <Search className="w-4 h-4 inline mr-1" />
              Univariate
            </button>
            <button
              onClick={() => setActiveTab('multivariate')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'multivariate'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              <SlidersHorizontal className="w-4 h-4 inline mr-1" />
              Multivariate
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'univariate' ? (
            <UnivariateTab
              columns={columns}
              numericColumns={numericColumns}
              selectedColumn={selectedColumn}
              setSelectedColumn={setSelectedColumn}
              selectedMethod={selectedMethod}
              setSelectedMethod={setSelectedMethod}
              threshold={threshold}
              setThreshold={setThreshold}
              onDetect={handleDetectUnivariate}
              isLoading={isLoading}
            />
          ) : (
            <MultivariateTab
              columns={columns}
              numericColumns={numericColumns}
              selectedColumns={multivariateColumns}
              setSelectedColumns={setMultivariateColumns}
              contamination={contamination}
              setContamination={setContamination}
              onDetect={handleDetectMultivariate}
              isLoading={isLoading}
            />
          )}

          {/* Results */}
          <div className="mt-6">
            <AnomalyCard
              anomalies={anomalies}
              column={activeTab === 'univariate' ? selectedColumn : multivariateColumns.join(', ')}
              onExport={handleExport}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

interface UnivariateTabProps {
  columns: SchemaColumn[];
  numericColumns: string[];
  selectedColumn: string;
  setSelectedColumn: (value: string) => void;
  selectedMethod: string;
  setSelectedMethod: (value: string) => void;
  threshold: number;
  setThreshold: (value: number) => void;
  onDetect: () => void;
  isLoading: boolean;
}

function UnivariateTab({
  columns,
  numericColumns,
  selectedColumn,
  setSelectedColumn,
  selectedMethod,
  setSelectedMethod,
  threshold,
  setThreshold,
  onDetect,
  isLoading,
}: UnivariateTabProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Column</label>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            className="input"
          >
            {numericColumns.map((col: string) => (
              <option key={col} value={col}>{col}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
          <select
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value)}
            className="input"
          >
            {univariateMethods.map(m => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Threshold {selectedMethod === 'zscore' ? '(std devs)' : selectedMethod === 'iqr' ? '(multiplier)' : ''}
          </label>
          <input
            type="number"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            step="0.1"
            min="0.1"
            max="10"
            className="input"
          />
        </div>
      </div>

      <div className="p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>Method:</strong> {univariateMethods.find(m => m.value === selectedMethod)?.desc}
        </p>
      </div>

      <button
        onClick={onDetect}
        disabled={isLoading || !selectedColumn}
        className="btn-primary flex items-center gap-2"
      >
        {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
        {isLoading ? 'Detecting...' : 'Detect Anomalies'}
      </button>
    </div>
  );
}

function isNumericType(type: string) {
  const normalized = type.toLowerCase();
  return ['int', 'float', 'double', 'decimal', 'numeric', 'number'].some(t => normalized.includes(t));
}

interface MultivariateTabProps {
  columns: SchemaColumn[];
  numericColumns: string[];
  selectedColumns: string[];
  setSelectedColumns: (value: string[] | ((prev: string[]) => string[])) => void;
  contamination: number;
  setContamination: (value: number) => void;
  onDetect: () => void;
  isLoading: boolean;
}

function MultivariateTab({
  columns,
  numericColumns,
  selectedColumns,
  setSelectedColumns,
  contamination,
  setContamination,
  onDetect,
  isLoading,
}: MultivariateTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Columns (numeric only)</label>
        <div className="flex flex-wrap gap-2">
          {numericColumns.map((col: string) => (
            <button
              key={col}
              onClick={() => setSelectedColumns(prev =>
                prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
              )}
              className={clsx(
                'px-3 py-1.5 text-sm rounded-lg border transition-colors',
                selectedColumns.includes(col)
                  ? 'bg-primary-600 text-white border-primary-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-primary-300'
              )}
            >
              {col}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Contamination ({contamination.toFixed(2)})
        </label>
        <input
          type="range"
          min="0.01"
          max="0.5"
          step="0.01"
          value={contamination}
          onChange={(e) => setContamination(Number(e.target.value))}
          className="w-full"
        />
        <p className="text-sm text-gray-500 mt-1">Expected proportion of outliers in the data</p>
      </div>

      <div className="p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>Isolation Forest:</strong> ML-based anomaly detection that isolates observations
          by randomly selecting a feature and then randomly selecting a split value between
          the maximum and minimum values of the selected feature.
        </p>
      </div>

      <button
        onClick={onDetect}
        disabled={isLoading || selectedColumns.length === 0}
        className="btn-primary flex items-center gap-2"
      >
        {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
        {isLoading ? 'Detecting...' : 'Detect Multivariate Anomalies'}
      </button>
    </div>
  );
}
