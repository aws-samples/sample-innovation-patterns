// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { useEffect } from 'react'
import { Outlet, useNavigation } from 'react-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar'
import { AppSidebar } from '@/components/app-sidebar'
import { RequireAuth } from '@/auth/RequireAuth'
import { SiteHeader } from '@/components/site-header'
import { DrawerPanelProvider } from '@/components/drawer-panel-provider'
import { RightDrawer } from '@/components/right-drawer'

NProgress.configure({ showSpinner: false })

export function RootLayout() {
  const navigation = useNavigation()

  useEffect(() => {
    if (navigation.state === 'loading') {
      NProgress.start()
    } else {
      NProgress.done()
    }
  }, [navigation.state])

  return (
    <RequireAuth>
      <DrawerPanelProvider>
        <SidebarProvider
          style={
            {
              '--sidebar-width': 'calc(var(--spacing) * 72)',
            } as React.CSSProperties
          }
        >
          <AppSidebar variant="inset" />
          <SidebarInset className="md:peer-data-[variant=inset]:m-0 md:peer-data-[variant=inset]:rounded-none md:peer-data-[variant=inset]:peer-data-[state=collapsed]:ml-0">
            <RightDrawer>
              <SiteHeader />
              <div className="flex flex-1 flex-col">
                <Outlet />
              </div>
            </RightDrawer>
          </SidebarInset>
        </SidebarProvider>
      </DrawerPanelProvider>
    </RequireAuth>
  )
}
