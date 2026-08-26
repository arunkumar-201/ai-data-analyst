import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { datasetsApi } from '../services/api';
import type { DatasetInfo } from '../types';
import {
  Database,
  Trash2,
  Eye,
  Download,
  BarChart2,
  AlertTriangle,
  FileText,
  MoreVertical,
  ChevronRight,
  Check,
} from 'lucide-react';

function clsx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

interface DatasetCardProps {
  dataset: DatasetInfo;
  compact?: boolean;
}

export function DatasetCard({ dataset, compact = false }: DatasetCardProps) {
  const navigate = useNavigate();
  const { setCurrentDataset, removeDataset, currentDatasetId } = useAppStore();
  const isActive = currentDatasetId === dataset.dataset_id;
  const [showMenu, setShowMenu] = React.useState(false);

  const handleDelete = async () => {
    if (window.confirm(`Delete dataset "${dataset.original_filename}"? This cannot be undone.`)) {
      try {
        await datasetsApi.delete(dataset.dataset_id);
        removeDataset(dataset.dataset_id);
      } catch (error) {
        console.error('Failed to delete dataset:', error);
        alert('Failed to delete dataset');
      }
    }
    setShowMenu(false);
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

  if (compact) {
    return (
      <button
        onClick={() => setCurrentDataset(dataset.dataset_id)}
        className={clsx(
          'w-full text-left p-3 rounded-lg border transition-colors',
          isActive
            ? 'bg-primary-50 border-primary-300'
            : 'bg-white border-gray-200 hover:border-primary-300 hover:bg-gray-50'
        )}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
            <Database className="w-5 h-5 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-gray-900 truncate">{dataset.original_filename}</p>
            <p className="text-xs text-gray-500">
              {dataset.rows.toLocaleString()} rows × {dataset.columns} cols
            </p>
          </div>
          {isActive && (
            <div className="w-5 h-5 rounded-full bg-primary-600 flex items-center justify-center">
              <Check className="w-3 h-3 text-white" />
            </div>
          )}
        </div>
      </button>
    );
  }

  return (
    <div className="card group">
      <div className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className={clsx(
              'w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0',
              isActive ? 'bg-primary-100' : 'bg-gray-100'
            )}>
              <Database className={clsx('w-6 h-6', isActive ? 'text-primary-600' : 'text-gray-600')} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-gray-900 truncate">{dataset.original_filename}</h3>
                {isActive && (
                  <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
                    Active
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 mt-0.5 truncate">Table: {dataset.table_name}</p>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <BarChart2 className="w-3.5 h-3.5" />
                  {dataset.rows.toLocaleString()} rows
                </span>
                <span className="flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  {dataset.columns} columns
                </span>
                <span className="flex items-center gap-1">
                  <Download className="w-3.5 h-3.5" />
                  {formatSize(dataset.file_size_mb)}
                </span>
              </div>
            </div>
          </div>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="More options"
            >
              <MoreVertical className="w-5 h-5" />
            </button>

            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                  <button
                    onClick={() => { setCurrentDataset(dataset.dataset_id); setShowMenu(false); }}
                    className={clsx('w-full px-4 py-2 text-left text-sm flex items-center gap-2', isActive ? 'text-primary-600 bg-primary-50' : 'text-gray-700 hover:bg-gray-50')}
                  >
                    <Eye className="w-4 h-4" />
                    Set as Active
                  </button>
                  <button
                    onClick={() => { navigate(`/quality?dataset=${dataset.dataset_id}&tab=profile`); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-gray-700 hover:bg-gray-50"
                  >
                    <BarChart2 className="w-4 h-4" />
                    View Profile
                  </button>
                  <button
                    onClick={() => { navigate(`/quality?dataset=${dataset.dataset_id}`); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-gray-700 hover:bg-gray-50"
                  >
                    <AlertTriangle className="w-4 h-4" />
                    Data Quality
                  </button>
                  <button
                    onClick={() => { navigate(`/reports?dataset=${dataset.dataset_id}`); setShowMenu(false); }}
                    className="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-gray-700 hover:bg-gray-50"
                  >
                    <FileText className="w-4 h-4" />
                    Generate Report
                  </button>
                  <hr className="my-1 border-gray-100" />
                  <button
                    onClick={handleDelete}
                    className="w-full px-4 py-2 text-left text-sm flex items-center gap-2 text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
          <span>Created: {formatDate(dataset.created_at)}</span>
          {dataset.validation_report && (
            <span className="flex items-center gap-1">
              <span className={clsx(
                'px-1.5 py-0.5 rounded-full text-xs font-medium',
                dataset.validation_report.quality_score >= 80 ? 'bg-green-100 text-green-700' :
                dataset.validation_report.quality_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              )}>
                Quality: {dataset.validation_report.quality_score.toFixed(0)}%
              </span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}