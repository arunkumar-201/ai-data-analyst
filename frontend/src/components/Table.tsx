import React, { useMemo, useState } from 'react';
import type { ToolResult } from '../types';
import { ChevronUp, ChevronDown, Search, Download } from 'lucide-react';
import { clsx } from 'clsx';

interface TableProps {
  data: ToolResult;
  title?: string;
  maxRows?: number;
  showExport?: boolean;
  onExport?: (format: 'csv' | 'excel' | 'json') => void;
}

export function Table({ data, title, maxRows = 100, showExport = true, onExport }: TableProps) {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 50;

  const columns = data.columns || [];
  const rows = data.data || [];

  const filteredAndSortedRows = useMemo(() => {
    let result = rows;

    // Filter by search term
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(row =>
        columns.some(col => String(row[col] || '').toLowerCase().includes(term))
      );
    }

    // Sort
    if (sortConfig) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        if (aVal === bVal) return 0;
        const direction = sortConfig.direction === 'asc' ? 1 : -1;
        if (aVal === null || aVal === undefined) return direction;
        if (bVal === null || bVal === undefined) return -direction;
        return (aVal > bVal ? 1 : -1) * direction;
      });
    }

    return result;
  }, [rows, columns, searchTerm, sortConfig]);

  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * rowsPerPage;
    return filteredAndSortedRows.slice(start, start + rowsPerPage);
  }, [filteredAndSortedRows, currentPage]);

  const totalPages = Math.ceil(filteredAndSortedRows.length / rowsPerPage);

  const handleSort = (key: string) => {
    setSortConfig(current => ({
      key,
      direction: current?.key === key && current.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const getSortIcon = (key: string) => {
    if (sortConfig?.key !== key) return null;
    return sortConfig.direction === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />;
  };

  if (!data.success) {
    return (
      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{title || 'Query Results'}</h3>
          {data.error && <span className="text-sm text-red-600">{data.error}</span>}
        </div>
        <div className="p-8 text-center text-red-600">
          <p>Query failed: {data.error || 'Unknown error'}</p>
        </div>
      </div>
    );
  }

  if (!columns.length || !rows.length) {
    return (
      <div className="card">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{title || 'Query Results'}</h3>
          <span className="text-sm text-gray-500">{data.row_count || 0} rows</span>
        </div>
        <div className="p-8 text-center text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No data to display</p>
        </div>
      </div>
    );
  }

  const displayRows = paginatedRows.slice(0, maxRows);

  return (
    <div className="card">
      <div className="p-4 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold text-gray-900">{title || 'Query Results'}</h3>
          <span className="text-sm text-gray-500">
            Showing {displayRows.length} of {filteredAndSortedRows.length} rows ({data.row_count || rows.length} total)
          </span>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="input pl-10 w-64"
            />
          </div>
          {showExport && onExport && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onExport('csv')}
                className="btn-secondary text-sm flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                CSV
              </button>
              <button
                onClick={() => onExport('excel')}
                className="btn-secondary text-sm flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                Excel
              </button>
              <button
                onClick={() => onExport('json')}
                className="btn-secondary text-sm flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                JSON
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className={clsx(
                    'cursor-pointer select-none',
                    sortConfig?.key === col && 'bg-primary-50 text-primary-700'
                  )}
                  onClick={() => handleSort(col)}
                >
                  <div className="flex items-center gap-1">
                    <span>{col}</span>
                    {getSortIcon(col)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columns.map((col) => (
                  <td key={col}>
                    <div className="max-w-xs truncate" title={String(row[col] ?? '')}>
                      {row[col] === null || row[col] === undefined ? (
                        <span className="text-gray-400 italic">null</span>
                      ) : typeof row[col] === 'number' ? (
                        <span className="font-mono">{Number(row[col]).toLocaleString()}</span>
                      ) : (
                        String(row[col])
                      )}
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="p-4 border-t border-gray-100 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Page {currentPage} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="btn-secondary text-sm"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="btn-secondary text-sm"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}