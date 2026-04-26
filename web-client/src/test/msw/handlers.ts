// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { http, HttpResponse } from 'msw'

export const handlers = [
  // Passengers
  http.get('http://localhost/api/v1/passengers', () => {
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

  http.get('http://localhost/api/v1/passengers/:ticket', ({ params }) => {
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
  http.get('http://localhost/api/v1/projects', () => {
    return HttpResponse.json({
      data: [{ id: '1', name: 'Test Project', description: null, created_at: null }],
    })
  }),

  http.get('http://localhost/api/v1/projects/:id', ({ params }) => {
    return HttpResponse.json({
      data: { id: params.id, name: 'Test Project', description: null, created_at: null },
    })
  }),

  http.post('http://localhost/api/v1/projects', async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>
    return HttpResponse.json({
      data: { id: '2', name: body.name, description: body.description ?? null, created_at: null },
    })
  }),

  http.delete('http://localhost/api/v1/projects/:id', () => {
    return new HttpResponse(null, { status: 204 })
  }),

  // Jobs
  http.get('http://localhost/api/v1/jobs', () => {
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

  http.post('http://localhost/api/v1/jobs', () => {
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
