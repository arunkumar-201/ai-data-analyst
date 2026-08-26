import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/useAppStore';
import { chatApi, datasetsApi } from '../services/api';
import type { Session, DatasetInfo } from '../types';
import {
  History as HistoryIcon,
  Clock,
  MessageSquare,
  Database,
  ChevronDown,
  ChevronRight,
  Trash2,
  Search,
  Filter,
  Download,
  Eye,
  Loader2,
} from 'lucide-react';

function clsx(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export function History() {
  const navigate = useNavigate();
  const { datasets, sessions, setDatasets, setSessions, removeSession } = useAppStore();
  const [allSessions, setAllSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDataset, setFilterDataset] = useState<string>('all');
  const [expandedSession, setExpandedSession] = useState<string | null>(null);

  useEffect(() => {
    if (datasets.length === 0) {
      loadDatasets();
    }
  }, []);

  useEffect(() => {
    loadAllSessions();
  }, [datasets.length]);

  const loadDatasets = async () => {
    try {
      const response = await datasetsApi.list();
      setDatasets(response.data.datasets || []);
    } catch (error) {
      console.error('Failed to load datasets:', error);
    }
  };

  const loadAllSessions = async () => {
    setIsLoading(true);
    try {
      const all: Session[] = [];
      for (const dataset of datasets) {
        try {
          const response = await chatApi.listSessions(dataset.dataset_id);
          all.push(...(response.data.sessions || []));
        } catch (e) {
          console.error(`Failed to load sessions for ${dataset.dataset_id}:`, e);
        }
      }
      // Sort by updated_at descending
      all.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      setAllSessions(all);
      setSessions(all);
    } catch (error) {
      console.error('Failed to load all sessions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Delete this chat session?')) {
      try {
        // Find the dataset for this session
        const session = allSessions.find(s => s.session_id === sessionId);
        if (session?.dataset_id) {
          await chatApi.deleteSession(sessionId);
          removeSession(sessionId);
          setAllSessions(prev => prev.filter(s => s.session_id !== sessionId));
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
        alert('Failed to delete session');
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
    return date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getDatasetName = (datasetId?: string) => {
    return datasets.find(d => d.dataset_id === datasetId)?.original_filename || 'Unknown';
  };

  const getSessionPreview = (session: Session) => {
    const lastMessage = session.messages[session.messages.length - 1];
    if (lastMessage) {
      return lastMessage.content.slice(0, 80) + (lastMessage.content.length > 80 ? '...' : '');
    }
    return 'Empty conversation';
  };

  const filteredSessions = allSessions.filter(session => {
    const matchesSearch = searchTerm === '' ||
      session.messages.some(m => m.content.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesDataset = filterDataset === 'all' || session.dataset_id === filterDataset;
    return matchesSearch && matchesDataset;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
            <HistoryIcon className="w-6 h-6 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">History</h1>
            <p className="text-gray-500 mt-1">View all your chat sessions across datasets</p>
          </div>
        </div>
        <button
          onClick={loadAllSessions}
          disabled={isLoading}
          className="btn-secondary flex items-center gap-2"
        >
          <Loader2 className={clsx('w-4 h-4', isLoading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search messages..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>

          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={filterDataset}
              onChange={(e) => setFilterDataset(e.target.value)}
              className="input pl-10 w-auto"
            >
              <option value="all">All Datasets</option>
              {datasets.map(d => (
                <option key={d.dataset_id} value={d.dataset_id}>{d.original_filename}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Sessions List */}
      {isLoading ? (
        <div className="card p-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-4" />
          <p className="text-gray-500">Loading history...</p>
        </div>
      ) : filteredSessions.length === 0 ? (
        <div className="card p-12 text-center">
          <HistoryIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            {allSessions.length === 0 ? 'No chat history yet' : 'No matching sessions'}
          </h3>
          <p className="text-gray-500 mb-6">
            {allSessions.length === 0
              ? 'Start a conversation in the Chat page to see history here'
              : 'Try adjusting your search or filters'}
          </p>
          {allSessions.length === 0 && (
            <button onClick={() => navigate('/chat')} className="btn-primary">
              <MessageSquare className="w-4 h-4 mr-2" />
              Start Chatting
            </button>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {filteredSessions.length} session{filteredSessions.length !== 1 ? 's' : ''} found
            </p>
          </div>

          <div className="divide-y divide-gray-100">
            {filteredSessions.map(session => {
              const isExpanded = expandedSession === session.session_id;
              const dataset = datasets.find(d => d.dataset_id === session.dataset_id);

              return (
                <div key={session.session_id} className={clsx('hover:bg-gray-50 transition-colors', isExpanded && 'bg-gray-50')}>
                  <button
                    onClick={() => setExpandedSession(isExpanded ? null : session.session_id)}
                    className="w-full p-4 flex items-start justify-between gap-4 text-left"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3">
                        <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', dataset ? 'bg-primary-100' : 'bg-gray-100')}>
                          <MessageSquare className={clsx('w-4 h-4', dataset ? 'text-primary-600' : 'text-gray-500')} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 truncate">{getSessionPreview(session)}</p>
                          <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                              <Database className="w-3.5 h-3.5" />
                              {dataset ? dataset.original_filename : 'No dataset'}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5" />
                              {formatDate(session.updated_at)}
                            </span>
                            <span className="flex items-center gap-1">
                              <MessageSquare className="w-3.5 h-3.5" />
                              {session.messages.length} messages
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (session.dataset_id) {
                              navigate(`/chat?dataset=${session.dataset_id}&session=${session.session_id}`);
                            }
                          }}
                          className="btn-secondary text-sm flex items-center gap-1"
                          title="Continue this session"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Open</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteSession(session.session_id);
                          }}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete session"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                        <ChevronRight className={clsx('w-4 h-4 text-gray-400 transition-transform', isExpanded && 'rotate-90')} />
                      </div>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50">
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {session.messages.slice().reverse().map((message, idx) => (
                          <div
                            key={message.id}
                            className={clsx('flex gap-2', message.role === 'user' && 'flex-row-reverse')}
                          >
                            <div className={clsx('w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium', message.role === 'user' ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600')}>
                              {message.role === 'user' ? 'U' : 'A'}
                            </div>
                            <div className={clsx('max-w-[80%] rounded-lg px-3 py-2 text-sm', message.role === 'user' ? 'bg-primary-100 text-primary-900' : 'bg-white text-gray-900 border border-gray-200')}>
                              <p className="whitespace-pre-wrap truncate" title={message.content}>{message.content}</p>
                              <span className="text-xs opacity-60 mt-1 block">{formatDate(message.timestamp)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}