// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { Outlet } from 'react-router'
import { ModeToggle } from '@/components/mode-toggle'
import { ThemeSelector } from '@/components/theme-selector'
import { Separator } from '@/components/ui/separator'
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar'
import { SinkBreadcrumbs } from './components/sink-breadcrumbs'
import { SinkSidebar } from './components/sink-sidebar'

export function SinkLayout() {
  return (
    <SidebarProvider defaultOpen={true}>
      <SinkSidebar />
      <SidebarInset>
        <header className="bg-background sticky top-0 z-10 flex h-14 items-center border-b px-4">
          <SidebarTrigger />
          <Separator orientation="vertical" className="mr-4 ml-2 !h-4" />
          <SinkBreadcrumbs />
          <div className="ml-auto flex items-center gap-2">
            <ThemeSelector />
            <ModeToggle />
          </div>
        </header>
        <div className="flex flex-1 flex-col">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
