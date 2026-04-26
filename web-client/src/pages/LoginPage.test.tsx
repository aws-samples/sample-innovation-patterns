// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { render, screen } from '@testing-library/react'
import { LoginPage } from './LoginPage'

describe('LoginPage', () => {
  it('renders the heading', () => {
    render(<LoginPage />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Create an account')
  })

  it('renders email input', () => {
    render(<LoginPage />)
    expect(screen.getByPlaceholderText('name@example.com')).toBeInTheDocument()
  })

  it('renders sign-in and GitHub buttons', () => {
    render(<LoginPage />)
    expect(screen.getByRole('button', { name: /sign in with email/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /github/i })).toBeInTheDocument()
  })
})
