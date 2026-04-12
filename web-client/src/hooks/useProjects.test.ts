// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { renderHook, waitFor } from '@testing-library/react'
import { useProjectList, useProject } from './useProjects'
import { createWrapper } from '@/test/test-utils'

describe('useProjectList', () => {
  it('fetches and returns projects', async () => {
    const { result } = renderHook(() => useProjectList(), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(true)

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.projects).toHaveLength(1)
    expect(result.current.projects[0].name).toBe('Test Project')
  })

  it('provides error and refetch', async () => {
    const { result } = renderHook(() => useProjectList(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.error).toBeUndefined()
    expect(typeof result.current.refetch).toBe('function')
  })
})

describe('useProject', () => {
  it('fetches a single project by id', async () => {
    const { result } = renderHook(() => useProject('1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.project).toBeTruthy()
    expect(result.current.project?.name).toBe('Test Project')
  })

  it('skips query when id is undefined', () => {
    const { result } = renderHook(() => useProject(undefined), {
      wrapper: createWrapper(),
    })

    // Should not be loading since the query is skipped
    expect(result.current.isLoading).toBe(false)
    expect(result.current.project).toBeNull()
  })
})
