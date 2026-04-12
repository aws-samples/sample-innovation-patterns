// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { cn } from './utils'

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('a', 'b')).toBe('a b')
  })

  it('handles conditional classes', () => {
    expect(cn('base', false && 'hidden', 'extra')).toBe('base extra')
  })

  it('deduplicates Tailwind classes via twMerge', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2')
  })

  it('handles empty input', () => {
    expect(cn()).toBe('')
  })

  it('handles undefined and null values', () => {
    expect(cn('a', undefined, null, 'b')).toBe('a b')
  })
})
