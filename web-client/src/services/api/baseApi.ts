// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import {
  createApi,
  fetchBaseQuery,
  type FetchArgs,
  type FetchBaseQueryError,
  type BaseQueryFn,
} from '@reduxjs/toolkit/query/react'
// API_BASE_URL is read from runtime config (window.__CONFIG__), not build-time
// env vars. This allows the same build artifact to work in any environment.
// In local dev it's empty (Vite proxy handles /api routing).
// In production it's the full API Gateway URL (e.g., https://xxx.execute-api.../prod).
// See: docs/docs/solution/web-client/CONFIG.md
import { config } from '@/lib/config'
import { getIdToken } from '@/lib/auth'

export const API_BASE_URL = config.API_BASE_URL

let globalErrorHandler: ((error: FetchBaseQueryError) => void) | null = null

export const setGlobalErrorHandler = (handler: (error: FetchBaseQueryError) => void) => {
  globalErrorHandler = handler
}

const baseQueryWithErrorHandling: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  const result = await fetchBaseQuery({
    baseUrl: API_BASE_URL,
    prepareHeaders: (headers) => {
      const token = getIdToken()
      if (token) {
        headers.set('authorization', `Bearer ${token}`)
      }
      return headers
    },
  })(args, api, extraOptions)

  if (result.error && globalErrorHandler) {
    globalErrorHandler(result.error)
  }

  return result
}

export const baseApi = createApi({
  reducerPath: 'appApi',
  baseQuery: baseQueryWithErrorHandling,
  tagTypes: ['passengers', 'projects', 'jobs'],
  endpoints: () => ({}),
})
