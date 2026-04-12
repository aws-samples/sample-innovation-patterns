// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/msw/server'
import { renderWithProviders } from '@/test/test-utils'
import { JobsPage } from './JobsPage'

describe('JobsPage', () => {
  it('renders the page heading', () => {
    renderWithProviders(<JobsPage />, { route: '/jobs' })
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Jobs')
  })

  it('renders job data from the API', async () => {
    renderWithProviders(<JobsPage />, { route: '/jobs' })
    await waitFor(() => {
      expect(screen.getByText('passenger_analysis')).toBeInTheDocument()
    })
  })

  it('shows filter buttons', async () => {
    renderWithProviders(<JobsPage />, { route: '/jobs' })
    await waitFor(() => {
      expect(screen.getByText('passenger_analysis')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /failed/i })).toBeInTheDocument()
  })

  it('shows unavailable message when API fails', async () => {
    server.use(
      http.get('http://localhost/api/v1/jobs', () => {
        return new HttpResponse(null, { status: 500 })
      }),
    )
    renderWithProviders(<JobsPage />, { route: '/jobs' })
    await waitFor(() => {
      expect(screen.getByText('Background processing not available')).toBeInTheDocument()
    })
  })
})
