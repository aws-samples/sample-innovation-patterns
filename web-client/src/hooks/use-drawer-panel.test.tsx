// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { renderHook, act } from '@testing-library/react'
import type { ReactNode } from 'react'
import { DrawerPanelContext, type DrawerPanelContextValue } from '@/components/drawer-panel-context'
import { useDrawerPanel } from './use-drawer-panel'

describe('useDrawerPanel', () => {
  it('returns context values', () => {
    const mockContext: DrawerPanelContextValue = {
      panel: null,
      open: false,
      setOpen: vi.fn(),
      setPanel: vi.fn(),
    }

    const wrapper = ({ children }: { children: ReactNode }) => (
      <DrawerPanelContext.Provider value={mockContext}>{children}</DrawerPanelContext.Provider>
    )

    const { result } = renderHook(() => useDrawerPanel(), { wrapper })

    expect(result.current.panel).toBeNull()
    expect(result.current.open).toBe(false)
    expect(typeof result.current.setOpen).toBe('function')
    expect(typeof result.current.setPanel).toBe('function')
  })

  it('calls setPanel from context', () => {
    const setPanel = vi.fn()
    const mockContext: DrawerPanelContextValue = {
      panel: null,
      open: false,
      setOpen: vi.fn(),
      setPanel,
    }

    const wrapper = ({ children }: { children: ReactNode }) => (
      <DrawerPanelContext.Provider value={mockContext}>{children}</DrawerPanelContext.Provider>
    )

    const { result } = renderHook(() => useDrawerPanel(), { wrapper })

    act(() => {
      result.current.setPanel({ content: 'test', title: 'Test' })
    })

    expect(setPanel).toHaveBeenCalledWith({ content: 'test', title: 'Test' })
  })
})
