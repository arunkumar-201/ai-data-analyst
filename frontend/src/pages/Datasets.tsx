import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { datasetsApi, uploadApi } from '../services/api';
import type { DatasetInfo } from '../types';
import { UploadZone } from '../components/UploadZone';
import { DatasetCard } from '../components/DatasetCard';
import {
  Database,
  Search,
  Filter,
  ChevronDown,
  ChevronUp,
  Download,
  Eye,
  Trash2,
  BarChart2,
  AlertTriangle,
  FileText,
  MoreVertical,
  ArrowRight,
  Plus,
  X,
  Grid,
  List,
} from 'lucide-react';
import { clsx } from 'clsx';

export function Datasets() {
  const navigate = useNavigate();
  const { datasets, setDatasets, currentDatasetId, setCurrentDataset, removeDataset, setIsUploading } = useAppStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'size' | 'rows'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showUpload, setShowUpload] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const response = await datasetsApi.list();
      const datasetList = response.data?.datasets;
      if (!Array.isArray(datasetList)) {
        throw new Error('The server returned an invalid dataset list');
      }
      setDatasets(datasetList);
      setLoadError(null);
    } catch (error) {
      console.error('Failed to load datasets:', error);
      setLoadError(error instanceof Error ? error.message : 'Failed to load datasets');
    }
  };

  const handleUploadComplete = async (datasetIds: string[]) => {
    await loadDatasets();
    setShowUpload(false);
    if (datasetIds.length > 0) {
      setCurrentDataset(datasetIds[0]);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Delete this dataset? This cannot be undone.')) {
      try {
        await datasetsApi.delete(id);
        removeDataset(id);
      } catch (error) {
        console.error('Failed to delete:', error);
        alert('Failed to delete dataset');
      }
    }
  };

  const handleSetActive = (id: string) => {
    setCurrentDataset(id);
    navigate('/chat');
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

  const sortedDatasets = [...datasets].sort((a, b) => {
    let aVal: any, bVal: any;
    switch (sortBy) {
      case 'name':
        aVal = a.original_filename.toLowerCase();
        bVal = b.original_filename.toLowerCase();
        break;
      case 'date':
        aVal = new Date(a.created_at).getTime();
        bVal = new Date(b.created_at).getTime();
        break;
      case 'size':
        aVal = a.file_size_mb;
        bVal = b.file_size_mb;
        break;
      case 'rows':
        aVal = a.rows;
        bVal = b.rows;
        break;
    }
    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const filteredDatasets = sortedDatasets.filter(d =>
    d.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.table_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
          <p className="text-gray-500 mt-1">Manage your uploaded datasets</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowUpload(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Upload CSV
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>

          <div className="flex items-center gap-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="input w-auto"
            >
              <option value="date">Date Added</option>
              <option value="name">Name</option>
              <option value="size">File Size</option>
              <option value="rows">Row Count</option>
            </select>

            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="btn-secondary p-2"
              title={sortOrder === 'asc' ? 'Descending' : 'Ascending'}
            >
              {sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            <div className="flex items-center gap-1 border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={clsx('p-2', viewMode === 'grid' ? 'bg-primary-600 text-white' : 'text-gray-500 hover:bg-gray-100')}
              >
                <Grid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={clsx('p-2', viewMode === 'list' ? 'bg-primary-600 text-white' : 'text-gray-500 hover:bg-gray-100')}
              >
                <List className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Dataset List */}
      {loadError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700" role="alert">
          {loadError}
        </div>
      )}
      {filteredDatasets.length === 0 ? (
        <div className="card p-12 text-center">
          {datasets.length === 0 ? (
            <>
              <Database className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">No datasets yet</h3>
              <p className="text-gray-500 mb-6">Upload your first CSV file to get started</p>
              <button
                onClick={() => setShowUpload(true)}
                className="btn-primary"
              >
                Upload CSV
              </button>
            </>
          ) : (
            <>
              <Search className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-1">No matching datasets</h3>
              <p className="text-gray-500">Try adjusting your search or filters</p>
            </>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>Showing {filteredDatasets.length} of {datasets.length} datasets</span>
          </div>

          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDatasets.map(dataset => (
                <DatasetCard key={dataset.dataset_id} dataset={dataset} />
              ))}
            </div>
          ) : (
            <div className="card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Dataset</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Rows</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">Columns</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden lg:table-cell">Size</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider hidden md:table-cell">Added</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredDatasets.map(dataset => (
                      <tr key={dataset.dataset_id} className={clsx('hover:bg-gray-50', currentDatasetId === dataset.dataset_id && 'bg-primary-50')}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                              <Database className="w-5 h-5 text-primary-600" />
                            </div>
                            <div>
                              <p className="font-medium text-gray-900 truncate max-w-xs">{dataset.original_filename}</p>
                              <p className="text-xs text-gray-500">{dataset.table_name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 hidden md:table-cell text-sm text-gray-700">{dataset.rows.toLocaleString()}</td>
                        <td className="px-4 py-3 hidden lg:table-cell text-sm text-gray-700">{dataset.columns}</td>
                        <td className="px-4 py-3 hidden lg:table-cell text-sm text-gray-700">{formatSize(dataset.file_size_mb)}</td>
                        <td className="px-4 py-3 hidden md:table-cell text-sm text-gray-500">{formatDate(dataset.created_at)}</td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleSetActive(dataset.dataset_id)}
                              className={clsx('p-2 rounded-lg transition-colors', currentDatasetId === dataset.dataset_id ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:bg-gray-100')}
                              title="Set as active"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/quality?dataset=${dataset.dataset_id}`)}
                              className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                              title="Data Quality"
                            >
                              <AlertTriangle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/anomalies?dataset=${dataset.dataset_id}`)}
                              className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
                              title="Anomalies"
                            >
                              <Search className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(dataset.dataset_id)}
                              className="p-2 rounded-lg text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Upload CSV Files</h2>
              <button
                onClick={() => setShowUpload(false)}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <UploadZone onUploadComplete={handleUploadComplete} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}