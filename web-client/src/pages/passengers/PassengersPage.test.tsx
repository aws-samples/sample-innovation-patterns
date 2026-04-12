// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '@/test/msw/server'
import { renderWithProviders } from '@/test/test-utils'
import { PassengersPage } from './PassengersPage'

vi.mock('./components/data-table', () => ({
  DataTable: (props: { data: unknown[] }) => (
    <div data-testid="passengers-table">{props.data.length} passengers</div>
  ),
}))
vi.mock('./components/columns', () => ({
  columns: [],
}))
vi.mock('./components/sqs-unavailable-dialog', () => ({
  SqsUnavailableDialog: () => null,
}))

describe('PassengersPage', () => {
  it('renders the page heading', () => {
    renderWithProviders(<PassengersPage />)
    expect(screen.getByText('Titanic Passengers')).toBeInTheDocument()
  })

  it('shows loading indicator initially', () => {
    renderWithProviders(<PassengersPage />)
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('renders passenger data from the API', async () => {
    renderWithProviders(<PassengersPage />)
    await waitFor(() => {
      expect(screen.getByTestId('passengers-table')).toHaveTextContent('1 passengers')
    })
  })

  it('shows error message when API fails', async () => {
    server.use(
      http.get('http://localhost/api/v1/passengers', () => {
        return new HttpResponse(null, { status: 500 })
      }),
    )
    renderWithProviders(<PassengersPage />)
    await waitFor(() => {
      expect(screen.getByText('Failed to load passengers.')).toBeInTheDocument()
    })
  })
})
