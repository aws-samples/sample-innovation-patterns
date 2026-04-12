// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { RootErrorBoundary } from './RootErrorBoundary'

describe('RootErrorBoundary', () => {
  // Suppress React/router error logging during error boundary tests
  const originalError = console.error
  beforeEach(() => {
    console.error = vi.fn()
  })
  afterEach(() => {
    console.error = originalError
  })

  it('shows 404 message for not-found routes', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          element: <div>Home</div>,
          errorElement: <RootErrorBoundary />,
          children: [
            {
              path: 'missing',
              loader: () => {
                throw new Response('Not Found', { status: 404 })
              },
              element: <div />,
            },
          ],
        },
      ],
      { initialEntries: ['/missing'] },
    )

    render(<RouterProvider router={router} />)
    expect(await screen.findByText('Page not found')).toBeInTheDocument()
  })

  it('shows generic error title for thrown errors', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          errorElement: <RootErrorBoundary />,
          loader: () => {
            throw new Error('Test error')
          },
          element: <div />,
        },
      ],
      { initialEntries: ['/'] },
    )

    render(<RouterProvider router={router} />)
    expect(await screen.findByText('Something broke')).toBeInTheDocument()
  })

  it('renders navigation buttons', async () => {
    const router = createMemoryRouter(
      [
        {
          path: '/',
          errorElement: <RootErrorBoundary />,
          loader: () => {
            throw new Error('fail')
          },
          element: <div />,
        },
      ],
      { initialEntries: ['/'] },
    )

    render(<RouterProvider router={router} />)
    expect(await screen.findByText('Back to Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Reload')).toBeInTheDocument()
  })
})
