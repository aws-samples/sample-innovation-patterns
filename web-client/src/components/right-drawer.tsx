// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { IconHelp } from '@tabler/icons-react'
import { Button } from '@/components/ui/button'
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '@/components/ui/drawer'
import { useDrawerPanel } from '@/hooks/use-drawer-panel'

export function RightDrawer({ children }: { children: React.ReactNode }) {
  const { panel, open, setOpen } = useDrawerPanel()

  return (
    <Drawer direction="right" open={open} onOpenChange={setOpen}>
      {children}
      {panel && (
        <DrawerContent className="data-[vaul-drawer-direction=right]:sm:max-w-sm">
          <DrawerHeader>
            <DrawerTitle>{panel.title ?? 'Info'}</DrawerTitle>
          </DrawerHeader>
          <div className="no-scrollbar overflow-y-auto px-4 pb-4">{panel.content}</div>
        </DrawerContent>
      )}
    </Drawer>
  )
}

export function RightDrawerTrigger() {
  const { panel } = useDrawerPanel()
  if (!panel) return null

  return (
    <DrawerTrigger asChild>
      <Button variant="ghost" size="icon" className="size-8">
        <IconHelp className="size-4" />
        <span className="sr-only">Open help panel</span>
      </Button>
    </DrawerTrigger>
  )
}
