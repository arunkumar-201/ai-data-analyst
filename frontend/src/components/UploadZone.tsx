import React, { useState, useCallback, useRef } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { uploadApi } from '../services/api';
import {
  Upload,
  File,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Trash2,
} from 'lucide-react';
import { clsx } from 'clsx';

interface UploadZoneProps {
  onUploadComplete?: (datasetIds: string[]) => void;
}

interface FileUploadState {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  datasetId?: string;
}

export function UploadZone({ onUploadComplete }: UploadZoneProps) {
  const { setIsUploading, addDataset, setCurrentDataset, datasets } = useAppStore();
  const [files, setFiles] = useState<FileUploadState[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | undefined => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return 'Only CSV files are supported';
    }
    const maxSize = 200 * 1024 * 1024; // Matches backend default limit
    if (file.size > maxSize) {
      return 'File size exceeds 200MB limit';
    }
    return undefined;
  };

  const handleFiles = useCallback((fileList: FileList | File[]) => {
    const newFiles: FileUploadState[] = [];
    for (const file of Array.from(fileList)) {
      const error = validateFile(file);
      newFiles.push({
        file,
        status: error ? 'error' : 'pending',
        progress: 0,
        error,
      });
    }
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
    e.target.value = '';
  }, [handleFiles]);

  const removeFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  const uploadFile = async (fileState: FileUploadState, index: number) => {
    setFiles(prev => prev.map((f, i) => i === index ? { ...f, status: 'uploading' as const } : f));

    try {
      const response = await uploadApi.upload([fileState.file]);
      const datasetInfo = response.data?.uploaded?.[0];
      const datasetId = datasetInfo?.dataset_id;
      const originalFilename = datasetInfo?.original_filename || datasetInfo?.filename;

      if (
        datasetInfo &&
        datasetId &&
        typeof originalFilename === 'string' &&
        typeof datasetInfo.table_name === 'string' &&
        typeof datasetInfo.rows === 'number' &&
        typeof datasetInfo.columns === 'number'
      ) {
        addDataset({
          ...datasetInfo,
          original_filename: originalFilename,
          created_at: datasetInfo.created_at || new Date().toISOString(),
          file_size_mb: typeof datasetInfo.file_size_mb === 'number' ? datasetInfo.file_size_mb : 0,
        });
        setFiles(prev => prev.map((f, i) =>
          i === index ? { ...f, status: 'success' as const, progress: 100, datasetId } : f
        ));

        if (datasets.length === 0) {
          setCurrentDataset(datasetId);
        }

        return datasetId;
      } else {
        const uploadError = response.data?.errors?.[0]?.error;
        throw new Error(uploadError || 'No dataset ID returned');
      }
    } catch (error: any) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'error' as const,
          error: error.response?.data?.detail || error.message || 'Upload failed'
        } : f
      ));
      return null;
    }
  };

  const handleUploadAll = async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    const successfulIds: string[] = [];
    setIsUploading(true);
    try {
      for (let i = 0; i < pendingFiles.length; i++) {
        const originalIndex = files.findIndex(f => f === pendingFiles[i]);
        const datasetId = await uploadFile(pendingFiles[i], originalIndex);
        if (datasetId) {
          successfulIds.push(datasetId);
        }
      }

      if (successfulIds.length > 0 && onUploadComplete) {
        onUploadComplete(successfulIds);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'success'));
  };

  const hasErrors = files.some(f => f.status === 'error');
  const hasPending = files.some(f => f.status === 'pending');
  const allComplete = files.length > 0 && files.every(f => f.status !== 'pending' && f.status !== 'uploading');

  return (
    <div className="card">
      <div className="p-6">
        {/* Drop Zone */}
        <div
          className={clsx(
            'relative border-2 border-dashed rounded-xl p-8 text-center transition-colors',
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            multiple
            onChange={handleInputChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            aria-label="Upload CSV files"
          />

          <div className="relative z-10">
            <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-1">
              Drag & drop CSV files here, or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Maximum file size: 200MB per file
            </p>
          </div>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">
                Files ({files.length})
              </h4>
              <div className="flex items-center gap-2">
                {hasPending && (
                  <button
                    onClick={handleUploadAll}
                    disabled={files.some(f => f.status === 'uploading')}
                    className="btn-primary text-sm flex items-center gap-1"
                  >
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Upload All
                  </button>
                )}
                {allComplete && (
                  <button
                    onClick={clearCompleted}
                    className="btn-secondary text-sm"
                  >
                    Clear Completed
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {files.map((fileState, index) => (
                <div
                  key={index}
                  className={clsx(
                    'flex items-center gap-4 p-3 rounded-lg border transition-colors',
                    fileState.status === 'success' && 'bg-green-50 border-green-200',
                    fileState.status === 'error' && 'bg-red-50 border-red-200',
                    fileState.status === 'uploading' && 'bg-blue-50 border-blue-200',
                    fileState.status === 'pending' && 'bg-gray-50 border-gray-200'
                  )}
                >
                  <File className={clsx(
                    'w-5 h-5 flex-shrink-0',
                    fileState.status === 'success' && 'text-green-500',
                    fileState.status === 'error' && 'text-red-500',
                    fileState.status === 'uploading' && 'text-blue-500 animate-spin',
                    fileState.status === 'pending' && 'text-gray-400'
                  )} />

                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{fileState.file.name}</p>
                    <div className="flex items-center gap-3 text-sm text-gray-500 mt-0.5">
                      <span>{(fileState.file.size / 1024 / 1024).toFixed(2)} MB</span>
                      {fileState.status === 'uploading' && (
                        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-600 transition-all duration-300"
                            style={{ width: `${fileState.progress}%` }}
                          />
                        </div>
                      )}
                      {fileState.status === 'success' && (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Uploaded
                        </span>
                      )}
                      {fileState.status === 'error' && (
                        <span className="text-red-600 flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" />
                          {fileState.error}
                        </span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => removeFile(index)}
                    disabled={fileState.status === 'uploading'}
                    className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors disabled:opacity-50"
                    aria-label="Remove file"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Stats */}
        {datasets.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="font-medium text-gray-900 mb-3">Uploaded Datasets</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {datasets.slice(0, 6).map(dataset => (
                <div
                  key={dataset.dataset_id}
                  className="p-3 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors cursor-pointer"
                >
                  <p className="font-medium text-gray-900 truncate">{dataset.original_filename}</p>
                  <p className="text-sm text-gray-500">
                    {dataset.rows.toLocaleString()} rows × {dataset.columns} columns
                  </p>
                </div>
              ))}
              {datasets.length > 6 && (
                <div className="p-3 rounded-lg border border-gray-200 bg-gray-50 text-center">
                  <p className="text-gray-500">+{datasets.length - 6} more datasets</p>
                  <p className="text-sm text-gray-400">Go to Datasets page to view all</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
