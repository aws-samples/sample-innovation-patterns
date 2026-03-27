import { useContext } from 'react'
import { DrawerPanelContext } from '@/components/drawer-panel-context'

export function useDrawerPanel() {
  return useContext(DrawerPanelContext)
}
