import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { chatApi, datasetsApi } from '../services/api';
import type { Session, DatasetInfo } from '../types';
import { ChatInterface } from '../components/ChatInterface';
import { DatasetCard } from '../components/DatasetCard';
import {
  MessageSquare,
  Plus,
  Trash2,
  Clock,
  Database,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Search,
  Loader2,
} from 'lucide-react';
import { clsx } from 'clsx';

export function Chat() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const {
    datasets,
    sessions,
    currentSessionId,
    currentDatasetId,
    setCurrentDataset,
    setCurrentSession,
    addSession,
    updateSession,
    removeSession,
    setDatasets,
    setSessions
  } = useAppStore();
  const [showDatasetPicker, setShowDatasetPicker] = useState(false);
  const [showSessionList, setShowSessionList] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Sync URL dataset param to store on mount
  useEffect(() => {
    const urlDataset = searchParams.get('dataset');
    if (urlDataset && urlDataset !== currentDatasetId) {
      setCurrentDataset(urlDataset);
    }
  }, [searchParams, currentDatasetId, setCurrentDataset]);

  // Load datasets on mount
  useEffect(() => {
    loadDatasets();
  }, []);

  // Load sessions when dataset changes
  useEffect(() => {
    if (currentDatasetId) {
      loadSessions(currentDatasetId, searchParams.get('session') || undefined);
    }
  }, [currentDatasetId, searchParams]);

  const loadDatasets = async () => {
    try {
      const response = await datasetsApi.list();
      setDatasets(response.data.datasets || []);
    } catch (error) {
      console.error('Failed to load datasets:', error);
    }
  };

  const loadSessions = async (datasetId: string, preferredSessionId?: string) => {
    setIsLoadingSessions(true);
    try {
      const response = await chatApi.listSessions(datasetId);
      setSessions(response.data.sessions || []);
      const preferredSession = response.data.sessions.find(
        session => session.session_id === preferredSessionId
      );
      const currentSession = response.data.sessions.find(
        session => session.session_id === currentSessionId
      );
      if (preferredSession) {
        setCurrentSession(preferredSession.session_id);
      } else if (currentSession) {
        setCurrentSession(currentSession.session_id);
      } else if (response.data.sessions.length > 0) {
        setCurrentSession(response.data.sessions[0].session_id);
      } else {
        setCurrentSession(null);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  const handleNewSession = async () => {
    if (!currentDatasetId) return;
    try {
      const response = await chatApi.createSession(currentDatasetId);
      const newSessionId = response.data.session_id;
      setCurrentSession(newSessionId);
      await loadSessions(currentDatasetId, newSessionId);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Delete this chat session?')) {
      try {
        await chatApi.deleteSession(sessionId);
        removeSession(sessionId);
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = diff / (1000 * 60 * 60);
    const days = diff / (1000 * 60 * 60 * 24);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    if (days < 7) return `${Math.floor(days)}d ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  const getSessionPreview = (session: Session) => {
    const lastMessage = session.messages[session.messages.length - 1];
    if (lastMessage) {
      return lastMessage.content.slice(0, 50) + (lastMessage.content.length > 50 ? '...' : '');
    }
    return 'New conversation';
  };

  if (!currentDatasetId) {
    return (
      <div className="card h-[calc(100vh-8rem)] flex flex-col">
        <div className="p-8 text-center">
          <Database className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a Dataset</h2>
          <p className="text-gray-500 mb-6">Choose a dataset from the sidebar or upload a new one</p>
          <button
            onClick={() => setShowDatasetPicker(true)}
            className="btn-primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Browse Datasets
          </button>
        </div>
      </div>
    );
  }

  const currentDataset = datasets.find(d => d.dataset_id === currentDatasetId);
  const currentSession = sessions.find(s => s.session_id === currentSessionId);

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Top Bar */}
      <div className="card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">Chat Analysis</h2>
            <p className="text-sm text-gray-500">
              {currentDataset?.original_filename || 'No dataset selected'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Dataset Picker */}
          <div className="relative">
            <button
              onClick={() => setShowDatasetPicker(!showDatasetPicker)}
              className="btn-secondary flex items-center gap-2"
            >
              <Database className="w-4 h-4" />
              <span className="hidden sm:inline">{currentDataset?.original_filename || 'Select Dataset'}</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {showDatasetPicker && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowDatasetPicker(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 w-72 bg-white rounded-lg shadow-lg border border-gray-200 py-1">
                  {datasets.map(dataset => (
                    <button
                      key={dataset.dataset_id}
                      onClick={() => {
                        setCurrentDataset(dataset.dataset_id);
                        setShowDatasetPicker(false);
                      }}
                      className={clsx('w-full px-4 py-2 text-left text-sm', currentDatasetId === dataset.dataset_id ? 'bg-primary-50 text-primary-700' : 'text-gray-700 hover:bg-gray-50')}
                    >
                      {dataset.original_filename}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Session List Toggle */}
          <button
            onClick={() => setShowSessionList(!showSessionList)}
            className={clsx('btn-secondary flex items-center gap-2', showSessionList && 'bg-primary-50 text-primary-700 border-primary-200')}
          >
            <Clock className="w-4 h-4" />
            <span className="hidden sm:inline">History</span>
          </button>

          {/* New Session */}
          <button
            onClick={handleNewSession}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Session Sidebar */}
        {showSessionList && (
          <aside className="w-72 bg-white border-r border-gray-200 flex flex-col hidden lg:flex">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Chat Sessions</h3>
              <button
                onClick={() => setShowSessionList(false)}
                className="lg:hidden p-1 text-gray-400 hover:text-gray-600"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {isLoadingSessions ? (
                <div className="p-4 text-center text-gray-500">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading sessions...
                </div>
              ) : sessions.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  <Clock className="w-12 h-12 mx-auto text-gray-300 mb-2" />
                  <p>No chat sessions yet</p>
                  <p className="text-sm">Start a new conversation</p>
                </div>
              ) : (
                <div className="p-2 space-y-1">
                  {sessions.map(session => (
                    <button
                      key={session.session_id}
                      onClick={() => setCurrentSession(session.session_id)}
                      className={clsx(
                        'w-full text-left p-3 rounded-lg transition-colors',
                        currentSessionId === session.session_id
                          ? 'bg-primary-50 text-primary-700'
                          : 'text-gray-700 hover:bg-gray-100'
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{getSessionPreview(session)}</p>
                          <p className="text-xs text-gray-500 mt-1">{formatDate(session.updated_at)}</p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(session.session_id);
                          }}
                          className="p-1 text-gray-400 hover:text-red-600 rounded opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </aside>
        )}

        {/* Chat Interface */}
        <div className="flex-1 min-w-0">
          <ChatInterface
            datasetId={currentDatasetId}
            sessionId={currentSessionId || undefined}
            onSessionCreated={(sessionId) => {
              setCurrentSession(sessionId);
              loadSessions(currentDatasetId);
            }}
          />
        </div>
      </div>

      {/* Mobile Session Drawer */}
      {showSessionList && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowSessionList(false)} />
          <aside className="absolute right-0 top-0 bottom-0 w-72 bg-white shadow-xl flex flex-col">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Chat Sessions</h3>
              <button onClick={() => setShowSessionList(false)} className="p-1 text-gray-400 hover:text-gray-600">
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {sessions.map(session => (
                <button
                  key={session.session_id}
                  onClick={() => { setCurrentSession(session.session_id); setShowSessionList(false); }}
                  className={clsx('w-full text-left p-3 rounded-lg transition-colors', currentSessionId === session.session_id ? 'bg-primary-50 text-primary-700' : 'text-gray-700 hover:bg-gray-100')}
                >
                  <p className="font-medium truncate">{getSessionPreview(session)}</p>
                  <p className="text-xs text-gray-500 mt-1">{formatDate(session.updated_at)}</p>
                </button>
              ))}
            </div>
          </aside>
        </div>
      )}

      {/* Dataset Picker Modal (Mobile) */}
      {showDatasetPicker && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setShowDatasetPicker(false)} />
          <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-xl shadow-xl max-h-[60vh] overflow-y-auto">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Select Dataset</h3>
              <button onClick={() => setShowDatasetPicker(false)} className="p-1 text-gray-400 hover:text-gray-600">
                <ChevronDown className="w-5 h-5" />
              </button>
            </div>
            <div className="p-2 space-y-1">
              {datasets.map(dataset => (
                <button
                  key={dataset.dataset_id}
                  onClick={() => { setCurrentDataset(dataset.dataset_id); setShowDatasetPicker(false); }}
                  className={clsx('w-full text-left p-3 rounded-lg transition-colors', currentDatasetId === dataset.dataset_id ? 'bg-primary-50 text-primary-700' : 'text-gray-700 hover:bg-gray-100')}
                >
                  {dataset.original_filename}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
