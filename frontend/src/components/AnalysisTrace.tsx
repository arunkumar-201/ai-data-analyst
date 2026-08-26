import React, { useState } from 'react';
import type { TraceStep } from '../types';
import {
  ChevronDown,
  ChevronRight,
  Terminal,
  Database,
  Code,
  BarChart2,
  Brain,
  Clock,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { clsx } from 'clsx';

interface AnalysisTraceProps {
  trace: TraceStep[];
  className?: string;
}

const stepIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  sql: Database,
  pandas: Code,
  chart: BarChart2,
  explanation: Brain,
  intent: Terminal,
  tool_call: Terminal,
  tool_result: Terminal,
  anomaly: AlertCircle,
  default: Terminal,
};

const stepLabels: Record<string, string> = {
  intent: 'Intent Detection',
  sql: 'SQL Generation',
  sql_execution: 'SQL Execution',
  pandas: 'Pandas Code Generation',
  pandas_execution: 'Pandas Execution',
  chart: 'Chart Generation',
  chart_selection: 'Chart Selection',
  explanation: 'Explanation Generation',
  anomaly: 'Anomaly Detection',
  tool_call: 'Tool Call',
  tool_result: 'Tool Result',
  context_update: 'Context Update',
};

export function AnalysisTrace({ trace, className }: AnalysisTraceProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  if (!trace || trace.length === 0) {
    return (
      <div className={clsx('card p-8 text-center', className)}>
        <div className="text-gray-400 mb-2">
          <Terminal className="w-12 h-12 mx-auto" />
        </div>
        <p className="text-gray-600">No analysis trace available</p>
      </div>
    );
  }

  return (
    <div className={clsx('card', className)}>
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-primary-600" />
          Analysis Trace
        </h3>
        <span className="text-sm text-gray-500">{trace.length} steps</span>
      </div>

      <div className="divide-y divide-gray-100">
        {trace.map((step, index) => {
          const Icon = stepIcons[step.step] || stepIcons.default;
          const isExpanded = expandedSteps.has(index);
          const hasDetails = step.details && Object.keys(step.details).length > 0;

          return (
            <div key={index} className="p-4 hover:bg-gray-50 transition-colors">
              <button
                onClick={() => {
                  setExpandedSteps(prev => {
                    const next = new Set(prev);
                    if (next.has(index)) next.delete(index);
                    else next.add(index);
                    return next;
                  });
                }}
                className="w-full flex items-start gap-3 text-left"
              >
                <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary-50 flex-shrink-0">
                  <Icon className="w-5 h-5 text-primary-600" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      {stepLabels[step.step] || step.step}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {step.details?.status && (
                    <div className="flex items-center gap-1 mt-1">
                      {step.details.status === 'success' ? (
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      ) : (
                        <AlertCircle className="w-3 h-3 text-red-500" />
                      )}
                      <span className={clsx(
                        'text-xs font-medium',
                        step.details.status === 'success' ? 'text-green-600' : 'text-red-600'
                      )}>
                        {step.details.status}
                      </span>
                    </div>
                  )}
                </div>

                {hasDetails && (
                  <div className="flex items-center gap-2 text-gray-400">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                )}
              </button>

              {isExpanded && hasDetails && (
                <div className="mt-4 ml-13 border-l-2 border-gray-200 pl-4">
                  <div className="space-y-2">
                    {Object.entries(step.details).map(([key, value]) => {
                      if (key === 'status') return null;

                      const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

                      return (
                        <div key={key} className="text-sm">
                          <span className="text-gray-500 font-medium">{displayKey}:</span>
                          <pre className="mt-1 p-3 bg-gray-100 rounded-lg text-gray-900 overflow-x-auto text-xs font-mono whitespace-pre-wrap">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </pre>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}