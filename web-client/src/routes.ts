import type { RouteObject } from 'react-router'
import { RootErrorBoundary } from '@/components/RootErrorBoundary'
import { RootLayout } from '@/layouts/RootLayout'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const routes: RouteObject[] = [
  {
    ErrorBoundary: RootErrorBoundary,
    children: [
      { path: '/login', Component: LoginPage },
      {
        path: '/',
        Component: RootLayout,
        children: [
          {
            index: true,
            lazy: () =>
              import('@/pages/DashboardPage').then((m) => ({
                Component: m.DashboardPage,
              })),
          },
          {
            path: 'passengers',
            lazy: () =>
              import('@/pages/passengers/PassengersPage').then((m) => ({
                Component: m.PassengersPage,
              })),
          },
          {
            path: 'passengers/:ticket',
            lazy: () =>
              import('@/pages/passengers/PassengerDetailPage').then((m) => ({
                Component: m.PassengerDetailPage,
              })),
          },
          {
            path: 'jobs',
            lazy: () =>
              import('@/pages/JobsPage').then((m) => ({
                Component: m.JobsPage,
              })),
          },
          {
            path: 'tasks',
            lazy: () =>
              import('@/pages/tasks/TasksPage').then((m) => ({
                Component: m.TasksPage,
              })),
          },
          {
            path: 'playground',
            lazy: () =>
              import('@/pages/playground/PlaygroundPage').then((m) => ({
                Component: m.PlaygroundPage,
              })),
          },
          {
            path: 'kb-playground',
            lazy: () =>
              import('@/pages/kb-playground/KBPlaygroundPage').then((m) => ({
                Component: m.KBPlaygroundPage,
              })),
          },
          {
            path: 'chat',
            lazy: () =>
              import('@/pages/chat/ChatPage').then((m) => ({
                Component: m.ChatPage,
              })),
          },
          {
            path: 'settings',
            lazy: () =>
              import('@/pages/SettingsPage').then((m) => ({
                Component: m.SettingsPage,
              })),
          },
          { path: '*', Component: NotFoundPage },
        ],
      },
    ],
  },
]
