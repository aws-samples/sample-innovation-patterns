// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
/**
 * Wires @assistant-ui/react ExternalStoreRuntime to the Agent Core Chat backend.
 */

import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react'
import {
  useExternalStoreRuntime,
  AssistantRuntimeProvider,
  type ExternalStoreThreadListAdapter,
  type ThreadMessageLike,
  type AppendMessage,
} from '@assistant-ui/react'

import {
  fetchSessions,
  fetchSessionEvents,
  deleteSession,
  streamChat,
  type SessionData,
} from '@/lib/chat-api'

const convertMessage = (msg: ThreadMessageLike): ThreadMessageLike => msg

export function AgentCoreRuntimeProvider({ children }: { children: ReactNode }) {
  const [sessions, setSessions] = useState<SessionData[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(undefined)
  const sessionIdRef = useRef<string | undefined>(undefined)
  const skipFetchRef = useRef(false)
  const [messages, setMessages] = useState<ThreadMessageLike[]>([])
  const [isRunning, setIsRunning] = useState(false)

  useEffect(() => {
    void fetchSessions().then(setSessions)
  }, [])

  useEffect(() => {
    sessionIdRef.current = currentSessionId
  }, [currentSessionId])

  useEffect(() => {
    if (skipFetchRef.current) {
      skipFetchRef.current = false
      return
    }
    // `cancelled` guards against a stale session's response (or the empty-state
    // reset) landing after the user has already switched threads. Keeping all
    // setMessages calls inside the async closure avoids synchronous
    // setState-in-effect.
    let cancelled = false
    const load = async () => {
      if (!currentSessionId) {
        if (!cancelled) setMessages([])
        return
      }
      const events = await fetchSessionEvents(currentSessionId)
      if (cancelled) return
      setMessages(
        events.map((e) => ({
          id: e.event_id,
          role: e.role as 'user' | 'assistant',
          content: [{ type: 'text' as const, text: e.content }],
          createdAt: new Date(e.timestamp),
        })),
      )
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [currentSessionId])

  const threadListAdapter: ExternalStoreThreadListAdapter = {
    threadId: currentSessionId,
    threads: sessions.map((s) => ({
      threadId: s.session_id,
      id: s.session_id,
      title: s.title,
      status: 'regular' as const,
    })),
    archivedThreads: [],
    onSwitchToNewThread: () => {
      setCurrentSessionId(undefined)
      setMessages([])
    },
    onSwitchToThread: (id) => setCurrentSessionId(id),
    onDelete: async (id) => {
      await deleteSession(id)
      setSessions((prev) => prev.filter((s) => s.session_id !== id))
      if (currentSessionId === id) {
        setCurrentSessionId(undefined)
        setMessages([])
      }
    },
    onRename: (id, title) => {
      setSessions((prev) => prev.map((s) => (s.session_id === id ? { ...s, title } : s)))
    },
  }

  const onNew = useCallback(async (message: AppendMessage) => {
    const text = message.content.find((c) => c.type === 'text')?.text ?? ''
    setMessages((prev) => [...prev, { role: 'user', content: [{ type: 'text' as const, text }] }])
    setIsRunning(true)

    let assistantText = ''
    for await (const chunk of streamChat(
      sessionIdRef.current ?? null,
      text,
      'us.anthropic.claude-sonnet-4-6',
    )) {
      if (chunk.text) {
        assistantText += chunk.text
        const snapshot = assistantText
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...last, content: [{ type: 'text' as const, text: snapshot }] },
            ]
          }
          return [
            ...prev,
            { role: 'assistant' as const, content: [{ type: 'text' as const, text: snapshot }] },
          ]
        })
      }
      if (chunk.done && chunk.session_id) {
        sessionIdRef.current = chunk.session_id
        skipFetchRef.current = true
        setCurrentSessionId(chunk.session_id)
        void fetchSessions().then(setSessions)
      }
    }
    setIsRunning(false)
  }, [])

  const runtime = useExternalStoreRuntime({
    messages,
    isRunning,
    onNew,
    convertMessage,
    adapters: { threadList: threadListAdapter },
  })

  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>
}
