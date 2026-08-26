import React, {
  useState,
  useRef,
  useEffect,
} from 'react';

import { useAppStore } from '../stores/useAppStore';
import { chatApi } from '../services/api';

import type {
  ChatMessage,
  ChatResponse,
  ToolResult,
} from '../types';

import {
  Send,
  Loader2,
  Copy,
  ChevronDown,
  Database,
  Code,
  BarChart2,
  Terminal,
  Plus,
  User,
  Bot,
  MessageSquare,
  Table as TableIcon,
} from 'lucide-react';

import { Chart } from './Chart';
import { Table } from './Table';
import { AnalysisTrace } from './AnalysisTrace';

function clsx(
  ...classes: (string | undefined | null | false)[]
) {
  return classes.filter(Boolean).join(' ');
}

interface ChatInterfaceProps {
  datasetId: string;
  sessionId?: string;
  onSessionCreated?: (sessionId: string) => void;
}

export function ChatInterface({
  datasetId,
  sessionId: initialSessionId,
  onSessionCreated,
}: ChatInterfaceProps) {
  const {
    sessions,
    currentSessionId,
    setCurrentSession,
    updateSession,
    setIsChatting,
  } = useAppStore();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  const sessionIdRef =
    useRef<string | null>(
      initialSessionId || null
    );

  useEffect(() => {
    sessionIdRef.current =
      initialSessionId || null;

    if (!initialSessionId) {
      setMessages([]);
    }
  }, [initialSessionId, datasetId]);

  // ---------------------------------------------------------
  // Load session messages
  // ---------------------------------------------------------

  useEffect(() => {
    const sessionId = sessionIdRef.current;

    if (!sessionId) {
      return;
    }

    const session = sessions.find(
      s => s.session_id === sessionId
    );

    if (session) {
      setMessages(session.messages || []);
    }
  }, [sessions, currentSessionId]);

  // ---------------------------------------------------------
  // Auto scroll
  // ---------------------------------------------------------

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
    });
  }, [messages]);

  // ---------------------------------------------------------
  // Send message
  // ---------------------------------------------------------

  const handleSend = async (
    e?: React.FormEvent
  ) => {
    e?.preventDefault();

    if (!input.trim() || isLoading) {
      return;
    }

    const question = input.trim();

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [
      ...prev,
      userMessage,
    ]);

    setInput('');
    setIsLoading(true);
    setIsChatting(true);

    try {
      const response =
        await chatApi.send(
          datasetId,
          question,
          sessionIdRef.current || undefined
        );

      const data: ChatResponse =
        response.data;

      // -----------------------------------------------------
      // Session handling
      // -----------------------------------------------------

      if (
        !sessionIdRef.current &&
        data.session_id
      ) {
        sessionIdRef.current =
          data.session_id;

        if (onSessionCreated) {
          onSessionCreated(
            data.session_id
          );
        }

        setCurrentSession(
          data.session_id
        );
      }

      // -----------------------------------------------------
      // Find intent
      // -----------------------------------------------------

      const intentStep =
        data.trace?.find(
          t =>
            t.step === 'intent' ||
            t.step === 'intent_detected'
        );

      // -----------------------------------------------------
      // IMPORTANT:
      // Store actual backend results.
      //
      // Previously the frontend only stored:
      // sql
      // pandas_code
      // trace
      //
      // But actual rows are inside:
      // data.results
      // -----------------------------------------------------

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content:
          data.answer ||
          data.explanation ||
          'No answer generated',
        timestamp:
          new Date().toISOString(),

        metadata: {
          sql: data.sql,
          pandas_code: data.pandas_code,

          chart_type:
            data.chart?.chart_type,
          chart: data.chart,

          intent:
            intentStep?.details
              ?.intent as string,

          trace: data.trace || [],

          // THIS IS THE IMPORTANT FIX
          results: data.results || [],
        },
      };

      setMessages(prev => [
        ...prev,
        assistantMessage,
      ]);

      // -----------------------------------------------------
      // Update session
      // -----------------------------------------------------

      const currentSession =
        sessions.find(
          s =>
            s.session_id ===
            sessionIdRef.current
        );

      if (currentSession) {
        updateSession(
          sessionIdRef.current!,
          {
            messages: [
              ...currentSession.messages,
              userMessage,
              assistantMessage,
            ],
          }
        );
      }
    } catch (error: any) {
      console.error(
        'Chat request failed:',
        error
      );

      const errorMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `Error: ${
          error?.response?.data?.detail ||
          error?.message ||
          'Failed to get response'
        }`,
        timestamp:
          new Date().toISOString(),
      };

      setMessages(prev => [
        ...prev,
        errorMessage,
      ]);
    } finally {
      setIsLoading(false);
      setIsChatting(false);
    }
  };

  // ---------------------------------------------------------
  // New session
  // ---------------------------------------------------------

  const handleNewSession =
    async () => {
      try {
        const response =
          await chatApi.createSession(
            datasetId
          );

        const newSessionId =
          response.data.session_id;

        sessionIdRef.current =
          newSessionId;

        setCurrentSession(
          newSessionId
        );

        setMessages([]);

        if (onSessionCreated) {
          onSessionCreated(
            newSessionId
          );
        }
      } catch (error) {
        console.error(
          'Failed to create session:',
          error
        );
      }
    };

  // ---------------------------------------------------------
  // Timestamp
  // ---------------------------------------------------------

  const formatTimestamp = (
    ts: string
  ) => {
    return new Date(
      ts
    ).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // ---------------------------------------------------------
  // Copy
  // ---------------------------------------------------------

  const copyToClipboard = (
    text: string
  ) => {
    navigator.clipboard.writeText(
      text
    );
  };

  // ---------------------------------------------------------
  // Get actual query results
  // ---------------------------------------------------------

  const getQueryResults = (
    message: ChatMessage
  ): ToolResult[] => {
    const results =
      message.metadata?.results;

    if (
      results &&
      Array.isArray(results)
    ) {
      return results.filter(
        result =>
          result &&
          result.success !== false &&
          Array.isArray(result.data)
      );
    }

    return [];
  };

  // ---------------------------------------------------------
  // Dataset missing
  // ---------------------------------------------------------

  if (!datasetId) {
    return (
      <div className="card h-full flex flex-col">
        <div className="p-8 text-center text-gray-500">
          <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />

          <p className="text-lg">
            Select a dataset to start chatting
          </p>

          <p className="text-sm mt-1">
            Choose a dataset from the sidebar
            or Datasets page
          </p>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------
  // UI
  // ---------------------------------------------------------

  return (
    <div className="card h-full flex flex-col">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="p-4 border-b border-gray-100 flex items-center justify-between">

        <div className="flex items-center gap-3">

          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-600" />
          </div>

          <div>
            <h3 className="font-semibold text-gray-900">
              Chat Analysis
            </h3>

            <p className="text-sm text-gray-500">
              Ask questions about your data
            </p>
          </div>

        </div>

        <button
          onClick={handleNewSession}
          className="btn-secondary text-sm flex items-center gap-1"
          title="New chat session"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>

      </div>

      {/* =====================================================
          MESSAGES
      ===================================================== */}

      <div className="flex-1 overflow-y-auto p-4 space-y-6">

        {/* Empty state */}

        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-12">

            <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />

            <p className="text-lg">
              Start a conversation
            </p>

            <p className="text-sm mt-1">
              Ask questions like:
            </p>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md mx-auto text-left">

              <button
                className="p-3 bg-gray-50 rounded-lg text-sm hover:bg-gray-100 cursor-pointer transition-colors text-left"
                onClick={() =>
                  setInput(
                    'Show me the first 10 rows'
                  )
                }
              >
                "Show me the first 10 rows"
              </button>

              <button
                className="p-3 bg-gray-50 rounded-lg text-sm hover:bg-gray-100 cursor-pointer transition-colors text-left"
                onClick={() =>
                  setInput(
                    'What are the column types?'
                  )
                }
              >
                "What are the column types?"
              </button>

              <button
                className="p-3 bg-gray-50 rounded-lg text-sm hover:bg-gray-100 cursor-pointer transition-colors text-left"
                onClick={() =>
                  setInput(
                    'Show distribution of numeric columns'
                  )
                }
              >
                "Show distribution of numeric columns"
              </button>

              <button
                className="p-3 bg-gray-50 rounded-lg text-sm hover:bg-gray-100 cursor-pointer transition-colors text-left"
                onClick={() =>
                  setInput(
                    'Find anomalies in the data'
                  )
                }
              >
                "Find anomalies in the data"
              </button>

            </div>
          </div>
        )}

        {/* ===================================================
            MESSAGE LOOP
        =================================================== */}

        {messages.map(message => {

          const queryResults =
            message.role === 'assistant'
              ? getQueryResults(message)
              : [];

          return (
            <div
              key={message.id}
              className={clsx(
                'flex gap-3',
                message.role === 'user' &&
                  'flex-row-reverse'
              )}
            >

              {/* Avatar */}

              <div
                className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',

                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600'
                )}
              >
                {message.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>

              {/* Message */}

              <div
                className={clsx(
                  'max-w-[90%] rounded-2xl px-4 py-3',

                  message.role === 'user'
                    ? 'bg-primary-600 text-white rounded-br-md'
                    : 'bg-white border border-gray-200 rounded-bl-md shadow-sm'
                )}
              >

                {/* Answer */}

                <div className="prose prose-sm max-w-none">

                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">
                      {message.content}
                    </p>
                  ) : (
                    <div className="text-gray-900 whitespace-pre-wrap">
                      {message.content}
                    </div>
                  )}

                </div>

                {/* =================================================
                    ASSISTANT METADATA
                ================================================= */}

                {message.role === 'assistant' &&
                  message.metadata && (

                  <div className="mt-3 space-y-3 border-t border-gray-100 pt-3">

                    {/* =============================================
                        SQL
                    ============================================= */}

                    {message.metadata.sql && (
                      <details className="group">

                        <summary className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">

                          <Database className="w-4 h-4" />

                          SQL Query

                          <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />

                        </summary>

                        <div className="mt-2 relative">

                          <button
                            onClick={() =>
                              copyToClipboard(
                                message.metadata!.sql!
                              )
                            }
                            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-xs"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>

                          <pre className="p-3 bg-gray-100 rounded-lg text-xs font-mono overflow-x-auto text-gray-900">
                            {message.metadata.sql}
                          </pre>

                        </div>

                      </details>
                    )}

                    {/* =============================================
                        PANDAS
                    ============================================= */}

                    {message.metadata.pandas_code && (
                      <details className="group">

                        <summary className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">

                          <Code className="w-4 h-4" />

                          Pandas Code

                          <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />

                        </summary>

                        <div className="mt-2 relative">

                          <button
                            onClick={() =>
                              copyToClipboard(
                                message.metadata!.pandas_code!
                              )
                            }
                            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-xs"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>

                          <pre className="p-3 bg-gray-100 rounded-lg text-xs font-mono overflow-x-auto text-gray-900">
                            {message.metadata.pandas_code}
                          </pre>

                        </div>

                      </details>
                    )}

                    {/* =============================================
                        QUERY RESULTS
                    ============================================= */}

                    {queryResults.length > 0 && (

                      <details
                        className="group"
                        open
                      >

                        <summary className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">

                          <TableIcon className="w-4 h-4" />

                          Query Results

                          <span className="text-xs text-gray-400">
                            ({queryResults.reduce(
                              (total, result) =>
                                total +
                                (result.row_count ??
                                  result.data?.length ??
                                  0),
                              0
                            )} rows)
                          </span>

                          <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />

                        </summary>

                        <div className="mt-2 space-y-4">

                          {queryResults.map(
                            (result, resultIndex) => {

                              const rows =
                                Array.isArray(
                                  result.data
                                )
                                  ? result.data
                                  : [];

                              if (
                                rows.length === 0
                              ) {
                                return (
                                  <div
                                    key={resultIndex}
                                    className="p-4 bg-gray-50 rounded-lg text-sm text-gray-500"
                                  >
                                    Query returned
                                    no rows.
                                  </div>
                                );
                              }

                              return (
                                <div
                                  key={resultIndex}
                                  className="overflow-x-auto"
                                >

                                  <Table
                                    data={{
                                      success: true,

                                      data: rows,

                                      columns:
                                        result.columns &&
                                        result.columns.length > 0
                                          ? result.columns
                                          : Object.keys(
                                              rows[0] || {}
                                            ),

                                      row_count:
                                        result.row_count ??
                                        rows.length,
                                    }}
                                    maxRows={20}
                                  />

                                </div>
                              );
                            }
                          )}

                        </div>

                      </details>
                    )}

                    {/* =============================================
                        CHART
                    ============================================= */}

                    {message.metadata.chart_type &&
                      message.metadata.chart && (

                      <details
                        className="group"
                        open
                      >

                        <summary className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">

                          <BarChart2 className="w-4 h-4" />

                          Visualization (
                          {message.metadata.chart_type}
                          )

                          <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />

                        </summary>

                        <div className="mt-2">

                          <Chart
                            chart={
                              message.metadata.chart
                            }
                          />

                        </div>

                      </details>
                    )}

                    {/* =============================================
                        ANALYSIS TRACE
                    ============================================= */}

                    {message.metadata.trace &&
                      message.metadata.trace.length >
                        0 && (

                      <details className="group">

                        <summary className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">

                          <Terminal className="w-4 h-4" />

                          Analysis Trace (
                          {
                            message.metadata.trace
                              .length
                          } steps)

                          <ChevronDown className="w-4 h-4 transition-transform group-open:rotate-180" />

                        </summary>

                        <div className="mt-2">
                          <AnalysisTrace
                            trace={
                              message.metadata.trace
                            }
                          />
                        </div>

                      </details>
                    )}

                  </div>
                )}

                {/* Timestamp */}

                <div className="mt-2 flex items-center justify-end">

                  <span className="text-xs text-gray-400">
                    {formatTimestamp(
                      message.timestamp
                    )}
                  </span>

                </div>

              </div>

            </div>
          );
        })}

        {/* =====================================================
            LOADING
        ===================================================== */}

        {isLoading && (
          <div className="flex gap-3">

            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-gray-600" />
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">

              <div className="flex items-center gap-2 text-gray-500">

                <Loader2 className="w-5 h-5 animate-spin" />

                <span>
                  Thinking...
                </span>

              </div>

            </div>

          </div>
        )}

        <div ref={messagesEndRef} />

      </div>

      {/* =======================================================
          INPUT
      ======================================================= */}

      <div className="p-4 border-t border-gray-100">

        <form
          onSubmit={handleSend}
          className="flex items-end gap-3"
        >

          <div className="flex-1 relative">

            <textarea
              value={input}
              onChange={e =>
                setInput(e.target.value)
              }
              placeholder="Ask a question about your data..."
              rows={1}
              className="input resize-none pr-12 min-h-[44px] max-h-32"
              onKeyDown={e => {

                if (
                  e.key === 'Enter' &&
                  !e.shiftKey
                ) {
                  e.preventDefault();
                  handleSend();
                }

              }}
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={
                !input.trim() ||
                isLoading
              }
              className="absolute bottom-2 right-2 p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Send message"
            >

              <Send className="w-5 h-5" />

            </button>

          </div>

        </form>

        <p className="text-xs text-gray-400 text-center mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>

      </div>

    </div>
  );
}
