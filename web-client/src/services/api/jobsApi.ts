// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { EventSource } from 'eventsource'
import { getIdToken } from '@/lib/auth'
import { baseApi, API_BASE_URL } from './baseApi'

export interface JobResponse {
  job_id: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  job_type: string
  input_data: Record<string, unknown>
  metadata: Record<string, unknown> | null
  error: string | null
  created_at: string
  updated_at: string
}

export interface JobCreate {
  job_type?: string
  input_data: Record<string, unknown>
}

export const jobsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    submitJob: build.mutation<JobResponse, JobCreate>({
      query: (body) => ({
        url: '/api/v1/jobs',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['jobs'],
    }),
    getJob: build.query<JobResponse, string>({
      query: (jobId) => `/api/v1/jobs/${jobId}`,
      providesTags: ['jobs'],
      // eslint-disable-next-line @typescript-eslint/unbound-method -- RTK Query callback pattern
      async onCacheEntryAdded(jobId, { updateCachedData, cacheEntryRemoved }) {
        const url = `${API_BASE_URL}/api/v1/sse/jobs/${jobId}`
        const es = new EventSource(url, {
          fetch: (input: RequestInfo | URL, init?: RequestInit) => {
            const token = getIdToken()
            // eslint-disable-next-line no-restricted-globals -- SSE EventSource requires raw fetch
            return fetch(input, {
              ...init,
              headers: { ...init?.headers, ...(token && { Authorization: `Bearer ${token}` }) },
            })
          },
        })
        es.onmessage = (event: MessageEvent<string>) => {
          if (event.data === '[DONE]') {
            es.close()
            return
          }
          try {
            const data = JSON.parse(event.data) as JobResponse
            if (data.job_id) {
              updateCachedData(() => data)
            }
          } catch {
            // ignore parse errors
          }
        }
        es.onerror = () => es.close()
        await cacheEntryRemoved
        es.close()
      },
    }),
    listJobs: build.query<
      JobResponse[],
      { limit?: number; status?: string; job_type?: string } | void
    >({
      query: (params) => ({
        url: '/api/v1/jobs',
        params: params ?? {},
      }),
      providesTags: ['jobs'],
    }),
  }),
  overrideExisting: false,
})

export const { useSubmitJobMutation, useGetJobQuery, useListJobsQuery } = jobsApi
