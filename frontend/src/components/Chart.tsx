import React, { useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import type { ChartResult } from '../types';

interface ChartProps {
  chart: ChartResult;
  className?: string;
  onExport?: (format: 'png' | 'html' | 'pdf') => void;
}

function clsx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export function Chart({ chart, className = '', onExport }: ChartProps) {
  const plotRef = useRef<Plot>(null);

  useEffect(() => {
    if (chart.success && chart.chart_json) {
      try {
        const plotData = JSON.parse(chart.chart_json);
        // Plotly will render automatically when data changes
      } catch (e) {
        console.error('Failed to parse chart JSON:', e);
      }
    }
  }, [chart.chart_json]);

  if (!chart.success) {
    return (
      <div className={clsx('card p-8 text-center', className)}>
        <div className="text-red-500 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p className="text-gray-600">Failed to render chart</p>
        {chart.error && <p className="text-sm text-gray-500 mt-1">{chart.error}</p>}
      </div>
    );
  }

  if (!chart.chart_json) {
    return (
      <div className={clsx('card p-8 text-center', className)}>
        <div className="text-gray-400 mb-2">
          <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <p className="text-gray-600">No chart data available</p>
      </div>
    );
  }

  try {
    const plotData = JSON.parse(chart.chart_json);
    const config: any = {
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d', 'resetScale2d'],
      toImageButtonOptions: {
        format: 'png',
        filename: chart.title || 'chart',
        height: 500,
        width: 700,
        scale: 2,
      },
      responsive: true,
    };

    return (
      <div className={clsx('card', className)}>
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">{chart.title || 'Chart'}</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 capitalize">{chart.chart_type}</span>
            {onExport && (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => onExport('png')}
                  className="p-1.5 text-gray-500 hover:text-gray-700 rounded transition-colors"
                  title="Export as PNG"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <button
                  onClick={() => onExport('html')}
                  className="p-1.5 text-gray-500 hover:text-gray-700 rounded transition-colors"
                  title="Export as HTML"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>
        <div className="p-4" style={{ minHeight: '400px' }}>
          <Plot
            ref={plotRef}
            data={plotData.data || []}
            layout={{ ...plotData.layout, autosize: true }}
            config={config}
            useResizeHandler={true}
            style={{ width: '100%', height: '400px' }}
          />
        </div>
      </div>
    );
  } catch (e) {
    return (
      <div className={clsx('card p-8 text-center', className)}>
        <p className="text-red-600">Error rendering chart: {String(e)}</p>
      </div>
    );
  }
}