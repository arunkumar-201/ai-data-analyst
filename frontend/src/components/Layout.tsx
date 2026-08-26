// Main layout component
import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import {
  LayoutDashboard,
  Database,
  MessageSquare,
  FileText,
  AlertTriangle,
  History,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Upload,
  BarChart2,
} from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Datasets', href: '/datasets', icon: Database },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
  { name: 'Data Quality', href: '/quality', icon: AlertTriangle },
  { name: 'Anomalies', href: '/anomalies', icon: BarChart2 },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'History', href: '/history', icon: History },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Layout() {
  const { sidebarOpen, toggleSidebar, currentDatasetId, datasets } = useAppStore();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 bg-white border-r border-gray-200 transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
          <div className={clsx('flex items-center gap-2', sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none')}>
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <BarChart2 className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg text-gray-900">AI Data Analyst</span>
          </div>
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href ||
              (item.href !== '/' && location.pathname.startsWith(item.href));
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                  !sidebarOpen && 'justify-center'
                )}
                title={sidebarOpen ? undefined : item.name}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {sidebarOpen && <span>{item.name}</span>}
              </NavLink>
            );
          })}
        </nav>

        {/* Current Dataset Indicator */}
        {currentDatasetId && sidebarOpen && (
          <div className="p-4 border-t border-gray-200">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">Current Dataset</p>
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-3">
              <p className="text-sm font-medium text-primary-900 truncate">
                {datasets.find(d => d.dataset_id === currentDatasetId)?.original_filename || currentDatasetId}
              </p>
              <p className="text-xs text-primary-700 mt-1">Active</p>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main
        className={clsx(
          'flex-1 min-h-screen transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}