// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useLocation } from 'react-router'
import { DrawerPanelContext, type DrawerPanelOptions } from '@/components/drawer-panel-context'

export function DrawerPanelProvider({ children }: { children: ReactNode }) {
  const [panel, setPanel] = useState<DrawerPanelOptions | null>(null)
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()

  useEffect(() => {
    // Subscribe to pathname changes and reset on navigation.
    // The setState calls here are in response to an external change
    // (route navigation), which is the intended use of effects.
    return () => {
      setOpen(false)
      setPanel(null)
    }
  }, [pathname])

  const set = useCallback((p: DrawerPanelOptions | null) => setPanel(p), [])

  return (
    <DrawerPanelContext.Provider value={{ panel, open, setOpen, setPanel: set }}>
      {children}
    </DrawerPanelContext.Provider>
  )
}
