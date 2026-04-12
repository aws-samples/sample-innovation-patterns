// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
/**
 * Thin fetch-based API client for the Agent Core Chat pattern.
 * Does NOT use RTK Query — ExternalStoreRuntime manages its own state.
 */

/* eslint-disable no-restricted-globals -- Chat API intentionally uses fetch, not RTK Query */

import { getIdToken } from '@/lib/auth'
import { config } from '@/lib/config'

const BASE = () => config.API_BASE_URL

function headers(): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getIdToken()
  if (token) h['Authorization'] = `Bearer ${token}`
  return h
}

export interface SessionData {
  session_id: string
  title: string
  created_at: string
}

export interface EventData {
  event_id: string
  role: string
  content: string
  timestamp: string
}

export async function fetchSessions(): Promise<SessionData[]> {
  const res = await fetch(`${BASE()}/api/v1/chat/sessions`, { headers: headers() })
  if (!res.ok) return []
  return (await res.json()) as SessionData[]
}

export async function fetchSessionEvents(id: string): Promise<EventData[]> {
  const res = await fetch(`${BASE()}/api/v1/chat/sessions/${id}`, { headers: headers() })
  if (!res.ok) return []
  return (await res.json()) as EventData[]
}

export async function deleteSession(id: string): Promise<void> {
  await fetch(`${BASE()}/api/v1/chat/sessions/${id}`, {
    method: 'DELETE',
    headers: headers(),
  })
}

export interface ChatChunk {
  text?: string
  done?: boolean
  session_id?: string
  error?: string
}

export async function* streamChat(
  sessionId: string | null,
  message: string,
  modelId: string,
): AsyncGenerator<ChatChunk> {
  const res = await fetch(`${BASE()}/api/v1/sse/chat`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ session_id: sessionId, message, model_id: modelId }),
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()!
    for (const line of lines) {
      if (line.startsWith('data: ') && line !== 'data: [DONE]') {
        yield JSON.parse(line.slice(6)) as ChatChunk
      }
    }
  }
}
