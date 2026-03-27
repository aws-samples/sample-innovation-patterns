import { createContext, type ReactNode } from 'react'

export interface DrawerPanelOptions {
  content: ReactNode
  title?: string
}

export interface DrawerPanelContextValue {
  panel: DrawerPanelOptions | null
  open: boolean
  setOpen: (open: boolean) => void
  setPanel: (options: DrawerPanelOptions | null) => void
}

export const DrawerPanelContext = createContext<DrawerPanelContextValue>({
  panel: null,
  open: false,
  setOpen: () => {},
  setPanel: () => {},
})
