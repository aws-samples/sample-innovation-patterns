// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { config } from '@/lib/config'
import type { ComponentProps, ComponentPropsWithoutRef } from 'react'
import {
  IconBolt,
  IconCamera,
  IconChartBar,
  IconCubeSpark,
  IconDashboard,
  IconDatabase,
  IconExternalLink,
  IconFileAi,
  IconFileDescription,
  IconHelp,
  IconMessageCircle,
  IconSettings,
  IconUsers,
  IconCreditCard,
  IconDotsVertical,
  IconLogout,
  IconNotification,
  IconUserCircle,
} from '@tabler/icons-react'
import { Link, useLocation } from 'react-router'

import { useAppAuth } from '@/auth/useAppAuth'
import { useAppUser } from '@/auth/useAppUser'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'
import { VersionBadge } from '@/components/version-badge'

const data = {
  navMain: [
    { title: 'Dashboard', url: '/', icon: IconDashboard },
    { title: 'Chat', url: '/chat', icon: IconMessageCircle, flag: 'chat' as const },
    { title: 'Passengers', url: '/passengers', icon: IconUsers },
    { title: 'Jobs', url: '/jobs', icon: IconBolt, flag: 'jobs' as const },
    { title: 'Playground', url: '/playground', icon: IconChartBar, flag: 'playground' as const },
    {
      title: 'KB Playground',
      url: '/kb-playground',
      icon: IconDatabase,
      flag: 'kb_playground' as const,
    },
  ],
  navClouds: [
    {
      title: 'Capture',
      icon: IconCamera,
      isActive: true,
      url: '#',
      items: [
        { title: 'Active Proposals', url: '#' },
        { title: 'Archived', url: '#' },
      ],
    },
    {
      title: 'Proposal',
      icon: IconFileDescription,
      url: '#',
      items: [
        { title: 'Active Proposals', url: '#' },
        { title: 'Archived', url: '#' },
      ],
    },
    {
      title: 'Prompts',
      icon: IconFileAi,
      url: '#',
      items: [
        { title: 'Active Proposals', url: '#' },
        { title: 'Archived', url: '#' },
      ],
    },
  ],
  navSecondary: [
    { title: 'Settings', url: '/settings', icon: IconSettings, external: false },
    { title: 'Get Help', url: '#', icon: IconHelp, external: false },
  ],
  samples: [
    { name: 'Kitchen Sink', url: '/sink', icon: IconCubeSpark, flag: 'kitchen_sink' as const },
    { name: 'Tabler Icons', url: 'https://tabler.io/icons', icon: IconExternalLink, external: true },
  ],
}

export function AppSidebar(props: ComponentProps<typeof Sidebar>) {
  const { pathname } = useLocation()
  const user = useAppUser()
  const { logout } = useAppAuth()

  const handleLogout = () => void logout()

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild className="data-[slot=sidebar-menu-button]:!p-1.5">
              <Link to="/">
                <IconCubeSpark className="!size-5" />
                <span className="text-base font-semibold">Innovation Patterns</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} currentPath={pathname} />
        <NavSamples items={data.samples} currentPath={pathname} />
        <NavSecondary items={data.navSecondary} className="mt-auto" currentPath={pathname} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user} onLogout={handleLogout} />
      </SidebarFooter>
    </Sidebar>
  )
}

function NavMain({ items, currentPath }: { items: typeof data.navMain; currentPath: string }) {
  const visibleItems = items.filter((item) => !item.flag || config.features[item.flag])

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          {visibleItems.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild tooltip={item.title} isActive={item.url === currentPath}>
                {'external' in item && item.external ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    <item.icon />
                    <span>{item.title}</span>
                  </a>
                ) : (
                  <Link to={item.url}>
                    <item.icon />
                    <span>{item.title}</span>
                  </Link>
                )}
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

function NavSamples({
  items,
  currentPath,
}: {
  items: typeof data.samples
  currentPath: string
}) {
  const visibleItems = items.filter((item) => !('flag' in item) || !item.flag || config.features[item.flag])

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel>Samples</SidebarGroupLabel>
      <SidebarMenu>
        {visibleItems.map((item) => (
          <SidebarMenuItem key={item.name}>
            <SidebarMenuButton asChild isActive={'url' in item && !('external' in item) && item.url === currentPath}>
              {'external' in item && item.external ? (
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  <item.icon />
                  <span>{item.name}</span>
                  <IconExternalLink className="ml-auto size-3 text-muted-foreground" />
                </a>
              ) : (
                <Link to={item.url}>
                  <item.icon />
                  <span>{item.name}</span>
                </Link>
              )}
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
}

function NavSecondary({
  items,
  currentPath,
  ...props
}: {
  items: typeof data.navSecondary
  currentPath: string
} & ComponentPropsWithoutRef<typeof SidebarGroup>) {
  return (
    <SidebarGroup {...props}>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild isActive={item.url === currentPath}>
                {item.external ? (
                  <a href={item.url} target="_blank" rel="noopener noreferrer">
                    <item.icon />
                    <span>{item.title}</span>
                    <IconExternalLink className="ml-auto size-3 text-muted-foreground" />
                  </a>
                ) : (
                  <Link to={item.url}>
                    <item.icon />
                    <span>{item.title}</span>
                  </Link>
                )}
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
        <VersionBadge />
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

function NavUser({
  user,
  onLogout,
}: {
  user: { name: string; email: string }
  onLogout: () => void
}) {
  const { isMobile } = useSidebar()
  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="h-8 w-8 rounded-lg grayscale">
                <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">{user.name}</span>
                <span className="text-muted-foreground truncate text-xs">{user.email}</span>
              </div>
              <IconDotsVertical className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            side={isMobile ? 'bottom' : 'right'}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <Avatar className="h-8 w-8 rounded-lg">
                  <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{user.name}</span>
                  <span className="text-muted-foreground truncate text-xs">{user.email}</span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem>
                <IconUserCircle />
                Account
              </DropdownMenuItem>
              <DropdownMenuItem>
                <IconCreditCard />
                Billing
              </DropdownMenuItem>
              <DropdownMenuItem>
                <IconNotification />
                Notifications
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={onLogout}>
              <IconLogout />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
