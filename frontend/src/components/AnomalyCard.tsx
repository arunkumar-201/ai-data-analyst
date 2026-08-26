import React from 'react';
import type { AnomalyResult } from '../types';
import { AlertTriangle, Info, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { clsx } from 'clsx';

interface AnomalyCardProps {
  anomalies: AnomalyResult[];
  column?: string;
  onExport?: () => void;
}

const severityStyles = {
  high: 'bg-red-50 border-red-200 text-red-800',
  medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  low: 'bg-blue-50 border-blue-200 text-blue-800',
};

const severityIcons = {
  high: AlertTriangle,
  medium: AlertTriangle,
  low: Info,
};

export function AnomalyCard({ anomalies, column, onExport }: AnomalyCardProps) {
  const [expanded, setExpanded] = React.useState(false);
  const displayAnomalies = expanded ? anomalies : anomalies.slice(0, 10);

  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="card p-8 text-center">
        <Info className="w-12 h-12 mx-auto text-gray-300 mb-2" />
        <p className="text-gray-600">No anomalies detected</p>
        <p className="text-sm text-gray-500 mt-1">The data appears to be within normal ranges</p>
      </div>
    );
  }

  const highCount = anomalies.filter(a => a.severity === 'high').length;
  const mediumCount = anomalies.filter(a => a.severity === 'medium').length;
  const lowCount = anomalies.filter(a => a.severity === 'low').length;

  return (
    <div className="card">
      <div className="p-4 border-b border-gray-100 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Anomalies Detected</h3>
            <p className="text-sm text-gray-500">
              {column ? `Column: ${column}` : 'Multivariate analysis'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-100 text-red-700">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              High: {highCount}
            </span>
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
              Medium: {mediumCount}
            </span>
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              Low: {lowCount}
            </span>
          </div>

          {anomalies.length > 10 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="btn-secondary text-sm flex items-center gap-1"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              {expanded ? 'Show Less' : `Show All (${anomalies.length})`}
            </button>
          )}

          {onExport && (
            <button
              onClick={onExport}
              className="btn-secondary text-sm flex items-center gap-1"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          )}
        </div>
      </div>

      <div className="divide-y divide-gray-100">
        {displayAnomalies.map((anomaly, index) => (
          <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
            <div className="flex items-start gap-3">
              <div className={clsx(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                severityStyles[anomaly.severity]
              )}>
                {React.createElement(severityIcons[anomaly.severity], { className: 'w-4 h-4' })}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">Row {anomaly.index}</span>
                  <span className={clsx(
                    'px-2 py-0.5 text-xs font-medium rounded-full',
                    severityStyles[anomaly.severity]
                  )}>
                    {anomaly.severity.toUpperCase()}
                  </span>
                </div>

                <p className="text-sm text-gray-600 mt-1">{anomaly.reason}</p>

                <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-500">
                  {anomaly.column && <span>Column: <span className="font-mono text-gray-700">{anomaly.column}</span></span>}
                  {anomaly.value !== undefined && <span>Value: <span className="font-mono text-gray-700">{anomaly.value}</span></span>}
                  {anomaly.z_score !== undefined && <span>Z-Score: <span className="font-mono text-gray-700">{anomaly.z_score.toFixed(2)}</span></span>}
                  {anomaly.anomaly_score !== undefined && <span>Score: <span className="font-mono text-gray-700">{anomaly.anomaly_score.toFixed(4)}</span></span>}
                  {anomaly.deviation_iqr !== undefined && <span>IQR Dev: <span className="font-mono text-gray-700">{anomaly.deviation_iqr.toFixed(2)}</span></span>}
                  {anomaly.lower_bound !== undefined && anomaly.upper_bound !== undefined && (
                    <span>Bounds: <span className="font-mono text-gray-700">[{anomaly.lower_bound.toFixed(2)}, {anomaly.upper_bound.toFixed(2)}]</span></span>
                  )}
                  {anomaly.direction && <span>Direction: <span className="font-mono text-gray-700">{anomaly.direction}</span></span>}
                </div>
              </div>
            </div>
          </div>
        ))}

        {anomalies.length > 10 && !expanded && (
          <div className="p-4 text-center text-gray-500 bg-gray-50 border-t border-gray-100">
            <p>Showing 10 of {anomalies.length} anomalies</p>
            <button
              onClick={() => setExpanded(true)}
              className="mt-2 text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Show all anomalies
            </button>
          </div>
        )}
      </div>
    </div>
  );
}