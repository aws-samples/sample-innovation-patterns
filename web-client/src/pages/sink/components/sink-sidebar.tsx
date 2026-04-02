import { type ComponentProps, useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router'
import {
  ArrowLeftIcon,
  ChevronRightIcon,
  ExternalLinkIcon,
  ListTodoIcon,
  SearchIcon,
} from 'lucide-react'

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Input } from '@/components/ui/input'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { componentRegistry } from '../component-registry'

export function SinkSidebar(props: ComponentProps<typeof Sidebar>) {
  const { pathname } = useLocation()
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    if (!search) return componentRegistry
    return Object.fromEntries(
      Object.entries(componentRegistry).filter(([, item]) =>
        item.name.toLowerCase().includes(search.toLowerCase())
      )
    )
  }, [search])

  return (
    <Sidebar side="left" collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link to="/">
                <ArrowLeftIcon />
                <span>Back to App</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <div className="px-2 group-data-[collapsible=icon]:hidden">
          <div className="relative">
            <SearchIcon className="text-muted-foreground absolute left-2.5 top-1/2 size-4 -translate-y-1/2" />
            <Input
              placeholder="Search components..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-8 pl-8"
            />
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        {(['registry:ui', 'registry:page'] as const).map((type) => {
          const items = Object.entries(filtered).filter(
            ([, i]) => i.type === type
          )
          if (!items.length) return null
          return (
            <Collapsible key={type} defaultOpen className="group/collapsible">
              <SidebarGroup>
                <CollapsibleTrigger asChild>
                  <SidebarGroupLabel className="cursor-pointer">
                    {type === 'registry:ui' ? 'Components' : 'Pages'}
                    <ChevronRightIcon className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarGroupLabel>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuSub>
                        {items.map(([key, item]) => (
                          <SidebarMenuSubItem key={key}>
                            <SidebarMenuSubButton
                              asChild
                              isActive={pathname === item.href}
                            >
                              <Link to={item.href}>
                                <span>{item.name}</span>
                                {item.label && (
                                  <span className="flex size-2 rounded-full bg-blue-500" />
                                )}
                              </Link>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        ))}
                      </SidebarMenuSub>
                    </SidebarMenuItem>
                  </SidebarMenu>
                </CollapsibleContent>
              </SidebarGroup>
            </Collapsible>
          )
        })}
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild isActive={pathname === '/tasks'}>
              <Link to="/tasks">
                <ListTodoIcon />
                <span>Tasks</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <a href="https://tabler.io/icons" target="_blank" rel="noopener noreferrer">
                <ExternalLinkIcon />
                <span>Icons</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
