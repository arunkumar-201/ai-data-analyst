// Global state management using Zustand
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DatasetInfo, Session, ChatMessage, Session as SessionType } from '../types';

interface AppState {
  // Datasets
  datasets: DatasetInfo[];
  currentDatasetId: string | null;
  setDatasets: (datasets: DatasetInfo[]) => void;
  addDataset: (dataset: DatasetInfo) => void;
  removeDataset: (id: string) => void;
  setCurrentDataset: (id: string | null) => void;

  // Chat sessions
  sessions: Session[];
  currentSessionId: string | null;
  setSessions: (sessions: Session[]) => void;
  addSession: (session: Session) => void;
  updateSession: (sessionId: string, updates: Partial<Session>) => void;
  removeSession: (id: string) => void;
  setCurrentSession: (id: string | null) => void;
  clearAllSessions: () => void;

  // UI state
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Loading states
  isUploading: boolean;
  setIsUploading: (loading: boolean) => void;
  isChatting: boolean;
  setIsChatting: (loading: boolean) => void;

  // Clear all data
  clearAllData: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Datasets
      datasets: [],
      currentDatasetId: null,
      setDatasets: (datasets) => set({ datasets }),
      addDataset: (dataset) => set((state) => ({ datasets: [...state.datasets, dataset] })),
      removeDataset: (id) => set((state) => ({
        datasets: state.datasets.filter(d => d.dataset_id !== id),
        currentDatasetId: state.currentDatasetId === id ? null : state.currentDatasetId,
      })),
      setCurrentDataset: (id) => set({ currentDatasetId: id }),

      // Sessions
      sessions: [],
      currentSessionId: null,
      setSessions: (sessions) => set({
  sessions: sessions.map(session => ({
    ...session,
    messages: Array.isArray(session.messages) ? session.messages : [],
    context: session.context || {},
  })),
}),
      addSession: (session) => set((state) => ({
  sessions: [
    {
      ...session,
      messages: Array.isArray(session.messages) ? session.messages : [],
      context: session.context || {},
    },
    ...state.sessions,
  ],
})),
      updateSession: (sessionId, updates) => set((state) => ({
        sessions: state.sessions.map(s => s.session_id === sessionId ? { ...s, ...updates } : s),
      })),
      removeSession: (id) => set((state) => ({
        sessions: state.sessions.filter(s => s.session_id !== id),
        currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
      })),
      setCurrentSession: (id) => set({ currentSessionId: id }),
      clearAllSessions: () => set({ sessions: [], currentSessionId: null }),

      // UI
      sidebarOpen: true,
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // Loading
      isUploading: false,
      setIsUploading: (loading) => set({ isUploading: loading }),
      isChatting: false,
      setIsChatting: (loading) => set({ isChatting: loading }),

      // Clear all data
      clearAllData: () => set({ datasets: [], currentDatasetId: null, sessions: [], currentSessionId: null }),
    }),
    {
      name: 'ai-data-analyst-store',
      partialize: (state) => ({
        datasets: state.datasets,
        currentDatasetId: state.currentDatasetId,
        sessions: state.sessions,
        currentSessionId: state.currentSessionId,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);