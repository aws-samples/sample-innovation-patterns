// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useContext } from 'react'
import { DrawerPanelContext } from '@/components/drawer-panel-context'

export function useDrawerPanel() {
  return useContext(DrawerPanelContext)
}
