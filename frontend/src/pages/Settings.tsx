import React, { useState, useEffect } from 'react';
import { useAppStore } from '../stores/useAppStore';
import { chatApi, datasetsApi } from '../services/api';
import {
  Settings as SettingsIcon,
  Database,
  MessageSquare,
  Bell,
  Shield,
  Palette,
  Trash2,
  Download,
  Upload,
  Info,
  ChevronRight,
  Moon,
  Sun,
  Monitor,
  Save,
  Loader2,
  BarChart2,
  Check,
  History,
} from 'lucide-react';

export function Settings() {
  const { sidebarOpen, setSidebarOpen, datasets, removeDataset, sessions, removeSession, clearAllData } = useAppStore();
  const [activeTab, setActiveTab] = useState<'general' | 'appearance' | 'data' | 'about'>('general');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [autoSave, setAutoSave] = useState(true);
  const [showSqlTrace, setShowSqlTrace] = useState(true);
  const [maxHistoryItems, setMaxHistoryItems] = useState(50);
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');

  // Load settings from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' || 'system';
    const savedAutoSave = localStorage.getItem('autoSave') !== 'false';
    const savedShowSqlTrace = localStorage.getItem('showSqlTrace') !== 'false';
    const savedMaxHistory = localStorage.getItem('maxHistoryItems');
    setTheme(savedTheme);
    setAutoSave(savedAutoSave);
    setShowSqlTrace(savedShowSqlTrace);
    if (savedMaxHistory) setMaxHistoryItems(Number(savedMaxHistory));
    applyTheme(savedTheme);
  }, []);

  const applyTheme = (newTheme: 'light' | 'dark' | 'system') => {
    const root = document.documentElement;
    if (newTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    } else {
      root.classList.toggle('dark', newTheme === 'dark');
    }
    localStorage.setItem('theme', newTheme);
  };

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    applyTheme(newTheme);
  };

  const handleExportSettings = async () => {
    setIsExporting(true);
    try {
      const settings = {
        theme,
        autoSave,
        showSqlTrace,
        maxHistoryItems,
        exportedAt: new Date().toISOString(),
        datasets: datasets.map(d => ({
          dataset_id: d.dataset_id,
          original_filename: d.original_filename,
          rows: d.rows,
          columns: d.columns,
          table_name: d.table_name,
          created_at: d.created_at,
        })),
        sessions: sessions.map(s => ({
          session_id: s.session_id,
          dataset_id: s.dataset_id,
          messageCount: s.messages.length,
          created_at: s.created_at,
          updated_at: s.updated_at,
        })),
      };

      const content = exportFormat === 'json'
        ? JSON.stringify(settings, null, 2)
        : [
            ['type', 'id', 'name', 'rows', 'columns', 'created_at'],
            ...datasets.map(dataset => [
              'dataset', dataset.dataset_id, dataset.original_filename,
              String(dataset.rows), String(dataset.columns), dataset.created_at,
            ]),
            ...sessions.map(session => [
              'session', session.session_id, '', '', '', session.created_at,
            ]),
          ].map(row => row.map(value => `"${String(value).replace(/"/g, '""')}"`).join(',')).join('\n');
      const extension = exportFormat;
      const blob = new Blob([content], { type: exportFormat === 'json' ? 'application/json' : 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-data-analyst-settings-${new Date().toISOString().split('T')[0]}.${extension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export settings');
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportSettings = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target?.result as string);
        if (data.theme) {
          handleThemeChange(data.theme);
        }
        if (data.autoSave !== undefined) {
          setAutoSave(data.autoSave);
          localStorage.setItem('autoSave', String(data.autoSave));
        }
        if (data.showSqlTrace !== undefined) {
          setShowSqlTrace(data.showSqlTrace);
          localStorage.setItem('showSqlTrace', String(data.showSqlTrace));
        }
        if (data.maxHistoryItems) {
          setMaxHistoryItems(data.maxHistoryItems);
          localStorage.setItem('maxHistoryItems', String(data.maxHistoryItems));
        }
        alert('Settings imported successfully');
      } catch (error) {
        console.error('Import failed:', error);
        alert('Failed to import settings');
      }
      e.target.value = '';
    };
    reader.readAsText(file);
  };

  const handleClearAllData = async () => {
    if (window.confirm('This will delete ALL datasets, chat sessions, and settings. This cannot be undone. Are you sure?')) {
      if (window.confirm('Final confirmation: Delete everything?')) {
        try {
          await Promise.all([
            ...datasets.map(dataset => datasetsApi.delete(dataset.dataset_id)),
            ...sessions.map(session => chatApi.deleteSession(session.session_id)),
          ]);
          clearAllData();
          localStorage.clear();
          alert('All data cleared');
        } catch (error) {
          console.error('Clear all data failed:', error);
          alert('Failed to clear all data');
        }
      }
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'data', label: 'Data Management', icon: Database },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
          <SettingsIcon className="w-6 h-6 text-gray-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Configure your preferences and manage data</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 px-4 overflow-x-auto" aria-label="Settings tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={clsx(
                  'py-3 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap flex items-center gap-1',
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* General Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6 max-w-2xl">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Application</h3>
                <div className="space-y-4">
                  <SettingItem
                    label="Auto-save sessions"
                    description="Automatically save chat sessions and context"
                    icon={Save}
                  >
                    <Toggle checked={autoSave} onChange={setAutoSave} />
                  </SettingItem>
                  <SettingItem
                    label="Show SQL trace in chat"
                    description="Display generated SQL queries in conversation history"
                    icon={Database}
                  >
                    <Toggle checked={showSqlTrace} onChange={setShowSqlTrace} />
                  </SettingItem>
                  <SettingItem
                    label="Max history items"
                    description="Maximum number of chat sessions to keep in history"
                    icon={History}
                  >
                    <input
                      type="number"
                      value={maxHistoryItems}
                      onChange={(e) => {
                        const val = Math.max(10, Math.min(500, Number(e.target.value) || 50));
                        setMaxHistoryItems(val);
                        localStorage.setItem('maxHistoryItems', String(val));
                      }}
                      min="10"
                      max="500"
                      className="input w-24"
                    />
                  </SettingItem>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Sidebar</h3>
                <div className="space-y-4">
                  <SettingItem
                    label="Sidebar open by default"
                    description="Keep the navigation sidebar expanded on load"
                    icon={ChevronRight}
                  >
                    <Toggle checked={sidebarOpen} onChange={setSidebarOpen} />
                  </SettingItem>
                </div>
              </div>
            </div>
          )}

          {/* Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="space-y-6 max-w-2xl">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Theme</h3>
                <div className="grid grid-cols-3 gap-4">
                  {(['light', 'dark', 'system'] as const).map(t => (
                    <button
                      key={t}
                      onClick={() => handleThemeChange(t)}
                      className={clsx(
                        'p-4 rounded-lg border-2 transition-colors text-left',
                        theme === t
                          ? 'border-primary-600 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <div className="flex items-center justify-center w-10 h-10 rounded-lg mb-2"
                        style={{
                          backgroundColor: t === 'light' ? '#ffffff' : t === 'dark' ? '#1f2937' : '#f3f4f6',
                          border: t === 'system' ? '1px solid #d1d5db' : 'none'
                        }}>
                        {t === 'light' && <Sun className="w-5 h-5 text-yellow-500" />}
                        {t === 'dark' && <Moon className="w-5 h-5 text-blue-400" />}
                        {t === 'system' && <Monitor className="w-5 h-5 text-gray-600" />}
                      </div>
                      <p className="font-medium text-gray-900 capitalize">{t}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {t === 'light' ? 'Always light mode' : t === 'dark' ? 'Always dark mode' : 'Follow system preference'}
                      </p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Data Management Tab */}
          {activeTab === 'data' && (
            <div className="space-y-6 max-w-2xl">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h3>
                <p className="text-gray-600 mb-4">Export all your settings, datasets metadata, and session history</p>
                <div className="flex items-center gap-4">
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value as any)}
                    className="input w-40"
                  >
                    <option value="json">JSON (full data)</option>
                    <option value="csv">CSV (summary only)</option>
                  </select>
                  <button
                    onClick={handleExportSettings}
                    disabled={isExporting}
                    className="btn-primary flex items-center gap-2"
                  >
                    {isExporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {isExporting ? 'Exporting...' : 'Export Settings'}
                  </button>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Settings</h3>
                <p className="text-gray-600 mb-4">Import previously exported settings</p>
                <div className="flex items-center gap-4">
                  <label className="btn-secondary flex items-center gap-2 cursor-pointer">
                    <Upload className="w-4 h-4" />
                    Choose File
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleImportSettings}
                      className="absolute inset-0 opacity-0 cursor-pointer"
                    />
                  </label>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Danger Zone</h3>
                <p className="text-gray-600 mb-4">These actions are irreversible</p>
                <div className="flex items-center gap-4">
                  <button
                    onClick={handleClearAllData}
                    className="btn-danger flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear All Data
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* About Tab */}
          {activeTab === 'about' && (
            <div className="max-w-2xl space-y-6">
              <div className="text-center py-8">
                <div className="w-20 h-20 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <BarChart2 className="w-10 h-10 text-primary-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">AI Data Analyst</h2>
                <p className="text-gray-500 mt-2">Version 1.0.0</p>
              </div>

              <div className="border-t border-gray-200 pt-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Features</h3>
                <ul className="space-y-2 text-gray-600">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Multi-CSV upload with validation</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Natural language chat with LLM</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> SQL & Pandas code generation</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Interactive Plotly visualizations</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Anomaly detection (Z-score, IQR, Isolation Forest)</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Data quality profiling & validation</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Conversation memory & context</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-green-500" /> Export to CSV, Excel, PDF, JSON</li>
                </ul>
              </div>

              <div className="border-t border-gray-200 pt-6 space-y-4">
                <h3 className="font-semibold text-gray-900">Technology Stack</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <p className="font-medium text-gray-900">Frontend</p>
                    <p>React 18 + TypeScript + Vite</p>
                    <p>Tailwind CSS + Plotly.js</p>
                    <p>Zustand + Axios</p>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Backend</p>
                    <p>FastAPI + Python 3.11+</p>
                    <p>DuckDB + Pandas</p>
                    <p>SciPy + scikit-learn</p>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6 space-y-2">
                <p className="text-sm text-gray-500">Built with modern web technologies for data analysis</p>
                <p className="text-sm text-gray-500">Privacy-focused: API keys never leave the backend</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SettingItem({ label, description, icon: Icon, children }: { label: string; description: string; icon: React.ComponentType<{ className?: string }>; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3 flex-1">
        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center border border-gray-200">
          <Icon className="w-5 h-5 text-gray-600" />
        </div>
        <div>
          <p className="font-medium text-gray-900">{label}</p>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      <div>{children}</div>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={clsx(
        'relative w-11 h-6 rounded-full transition-colors',
        checked ? 'bg-primary-600' : 'bg-gray-300'
      )}
      role="switch"
      aria-checked={checked}
    >
      <span className={clsx(
        'absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform',
        checked ? 'translate-x-5' : 'translate-x-0.5'
      )} />
    </button>
  );
}

function clsx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}