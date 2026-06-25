// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
//
// Shared MSW request handlers — used by BOTH the browser worker (src/mocks/browser.ts,
// active in `npm run dev` when MOCK_API is true) AND the Node test server
// (src/test/msw/server.ts, active under Vitest).
//
// URLs are RELATIVE (`/api/v1/...`) on purpose. A relative path resolves against:
//   - location.origin in the browser (dev: same origin the Vite proxy serves from), and
//   - jsdom's origin (http://localhost) under Vitest — where API_BASE_URL is set to
//     'http://localhost' (src/test/setup.ts), so RTK Query issues absolute
//     http://localhost/api/v1/... requests that MSW still matches by path.
// This single detail is what lets one handler set serve both environments.
//
// CONTRACT RULE: each response shape must mirror the matching app-lib DTO
// (routes/{name}_dto.py Pydantic serialization) so `npm run codegen` produces a
// typed client that drops in when MOCK_API is flipped off. See src/mocks/AGENTS.md.
import { http, HttpResponse } from 'msw'

export const handlers = [
  // Passengers
  http.get('/api/v1/passengers', () => {
    return HttpResponse.json([
      {
        ticket: 'A/5 21171',
        name: 'Test Passenger',
        pclass: 1,
        sex: 'male',
        age: 30,
        survived: true,
        embarked: 'S',
        fare: 71.28,
        sib_sp: 0,
        parch: 0,
      },
    ])
  }),

  http.get('/api/v1/passengers/:ticket', ({ params }) => {
    return HttpResponse.json({
      ticket: params.ticket,
      name: 'Test Passenger',
      pclass: 1,
      sex: 'male',
      age: 30,
      survived: true,
      embarked: 'S',
      fare: 71.28,
      sib_sp: 0,
      parch: 0,
    })
  }),

  // Projects
  http.get('/api/v1/projects', () => {
    return HttpResponse.json({
      data: [{ id: '1', name: 'Test Project', description: null, created_at: null }],
    })
  }),

  http.get('/api/v1/projects/:id', ({ params }) => {
    return HttpResponse.json({
      data: { id: params.id, name: 'Test Project', description: null, created_at: null },
    })
  }),

  http.post('/api/v1/projects', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({
      data: { id: '2', name: body.name, description: body.description ?? null, created_at: null },
    })
  }),

  http.delete('/api/v1/projects/:id', () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // Jobs
  http.get('/api/v1/jobs', () => {
    return HttpResponse.json([
      {
        job_id: 'j1',
        status: 'COMPLETED',
        job_type: 'passenger_analysis',
        input_data: { ticket: 'A/5 21171' },
        metadata: null,
        error: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:01:00Z',
      },
    ])
  }),

  http.post('/api/v1/jobs', () => {
    return HttpResponse.json({
      job_id: 'j-new',
      status: 'PENDING',
      job_type: 'passenger_analysis',
      input_data: {},
      metadata: null,
      error: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })
  }),
]
