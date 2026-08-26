import React from 'react';
import type { ValidationReport, ValidationIssue } from '../types';
import {
  AlertTriangle,
  CheckCircle,
  Info,
  XCircle,
  ChevronDown,
  ChevronUp,
  Filter,
  Download,
} from 'lucide-react';
import { clsx } from 'clsx';

interface QualityDashboardProps {
  report: ValidationReport;
  onExport?: () => void;
}

const severityConfig = {
  high: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', label: 'High' },
  medium: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'Medium' },
  low: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', label: 'Low' },
  info: { icon: Info, color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', label: 'Info' },
};

export function QualityDashboard({ report, onExport }: QualityDashboardProps) {
  const [filterSeverity, setFilterSeverity] = React.useState<'all' | 'high' | 'medium' | 'low' | 'info'>('all');
  const [expandedIssues, setExpandedIssues] = React.useState<Set<number>>(new Set());

  const filteredIssues = filterSeverity === 'all'
    ? report.issues
    : report.issues.filter(i => i.severity === filterSeverity);

  const severityCounts = {
    high: report.issues.filter(i => i.severity === 'high').length,
    medium: report.issues.filter(i => i.severity === 'medium').length,
    low: report.issues.filter(i => i.severity === 'low').length,
    info: report.issues.filter(i => i.severity === 'info').length,
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={clsx('w-12 h-12 rounded-xl flex items-center justify-center', getQualityBg(report.quality_score))}>
            <CheckCircle className={clsx('w-6 h-6', getQualityColor(report.quality_score))} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Data Quality Report</h3>
            <p className="text-sm text-gray-500">
              {report.rows.toLocaleString()} rows × {report.columns} columns
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className={clsx('px-4 py-2 rounded-xl text-2xl font-bold', getQualityColor(report.quality_score))}>
            {report.quality_score.toFixed(1)}%
          </div>
          {onExport && (
            <button onClick={onExport} className="btn-secondary text-sm flex items-center gap-1">
              <Download className="w-4 h-4" />
              Export Report
            </button>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-4 border-b border-gray-100 bg-gray-50">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-red-600">{severityCounts.high}</p>
            <p className="text-sm text-gray-500">High Severity</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-yellow-600">{severityCounts.medium}</p>
            <p className="text-sm text-gray-500">Medium Severity</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-blue-600">{severityCounts.low}</p>
            <p className="text-sm text-gray-500">Low Severity</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-2xl font-bold text-gray-600">{severityCounts.info}</p>
            <p className="text-sm text-gray-500">Info</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-gray-100 flex flex-wrap items-center gap-4">
        <Filter className="w-5 h-5 text-gray-400" />
        <div className="flex items-center gap-2 flex-wrap">
          {(['all', 'high', 'medium', 'low', 'info'] as const).map(sev => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={clsx(
                'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                filterSeverity === sev
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {sev === 'all' ? 'All Issues' : `${sev.charAt(0).toUpperCase() + sev.slice(1)} (${severityCounts[sev]})`}
            </button>
          ))}
        </div>
      </div>

      {/* Issues List */}
      <div className="divide-y divide-gray-100">
        {filteredIssues.length === 0 ? (
          <div className="p-8 text-center">
            <CheckCircle className="w-12 h-12 mx-auto text-green-400 mb-2" />
            <p className="text-gray-600">
              {filterSeverity === 'all'
                ? 'No data quality issues found!'
                : `No ${filterSeverity} severity issues found`}
            </p>
          </div>
        ) : (
          filteredIssues.map((issue, index) => {
            const config = severityConfig[issue.severity];
            const Icon = config.icon;
            const isExpanded = expandedIssues.has(index);
            const originalIndex = report.issues.indexOf(issue);

            return (
              <div key={originalIndex} className="p-4 hover:bg-gray-50 transition-colors">
                <button
                  onClick={() => {
                    setExpandedIssues(prev => {
                      const next = new Set(prev);
                      if (next.has(originalIndex)) next.delete(originalIndex);
                      else next.add(originalIndex);
                      return next;
                    });
                  }}
                  className="w-full flex items-start gap-3 text-left"
                >
                  <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', config.bg, config.border)}>
                    <Icon className={clsx('w-4 h-4', config.color)} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{issue.column || 'Dataset'}</span>
                      <span className={clsx('px-2 py-0.5 text-xs font-medium rounded-full', config.bg, config.color)}>
                        {config.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{issue.issue}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                      <span>Affected: <span className="font-mono">{issue.count.toLocaleString()}</span> ({issue.percentage.toFixed(1)}%)</span>
                      <span>Recommendation: {issue.recommendation}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-gray-400">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="mt-4 ml-11 border-l-2 border-gray-200 pl-4">
                    <div className="space-y-2 text-sm">
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-medium text-gray-700">Recommendation</p>
                        <p className="text-gray-600 mt-1">{issue.recommendation}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}