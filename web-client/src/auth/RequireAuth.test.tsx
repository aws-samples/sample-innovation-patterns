// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { render, screen } from '@testing-library/react'
import { RequireAuth } from './RequireAuth'

describe('RequireAuth', () => {
  it('renders children directly when auth is disabled', () => {
    render(
      <RequireAuth>
        <div data-testid="protected">Protected Content</div>
      </RequireAuth>,
    )

    expect(screen.getByTestId('protected')).toHaveTextContent('Protected Content')
  })

  it('does not wrap with OidcSecure when auth is disabled', () => {
    const { container } = render(
      <RequireAuth>
        <p>Visible</p>
      </RequireAuth>,
    )

    expect(container.querySelector('p')).toHaveTextContent('Visible')
  })
})
