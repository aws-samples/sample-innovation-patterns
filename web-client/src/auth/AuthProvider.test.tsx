// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { render, screen } from '@testing-library/react'
import { AuthProvider } from './AuthProvider'

describe('AuthProvider', () => {
  it('renders children directly when auth is disabled', () => {
    // isAuthEnabled is false (setup.ts sets empty OIDC values)
    render(
      <AuthProvider>
        <div data-testid="child">Hello</div>
      </AuthProvider>,
    )

    expect(screen.getByTestId('child')).toHaveTextContent('Hello')
  })

  it('does not wrap with OidcProvider when auth is disabled', () => {
    const { container } = render(
      <AuthProvider>
        <span>Content</span>
      </AuthProvider>,
    )

    // Should render just the span without any OIDC wrapper
    expect(container.querySelector('span')).toHaveTextContent('Content')
  })
})
