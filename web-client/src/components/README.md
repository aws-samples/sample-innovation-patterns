# components/

Shared layout and UI components used across pages.

## Contents

| File | Purpose |
|------|---------|
| `app-sidebar.tsx` | Left sidebar navigation |
| `site-header.tsx` | Top header with breadcrumbs, theme selector, mode toggle, drawer trigger |
| `drawer-panel-provider.tsx` | Context provider for route-specific right drawer panels |
| `right-drawer.tsx` | Right-side drawer (vaul) + `RightDrawerTrigger` icon button |
| `active-theme.tsx` | Theme configuration provider |
| `theme-selector.tsx` | Theme dropdown selector |
| `mode-toggle.tsx` | Light/dark mode toggle |
| `markdown-content.tsx` | Markdown renderer |
| `version-badge.tsx` | App version display |
| `RootErrorBoundary.tsx` | Top-level error boundary |
| `ui/` | shadcn/ui primitives — never edit directly |
| `assistant-ui/` | Chat UI components (assistant-ui library) |

## Right Drawer (Help Panel)

Route-specific right-side drawer inspired by the Cloudscape AppLayout help panel.
Pages opt in by calling `useDrawerPanel()` and setting content in a `useEffect`.

### Usage

1. Create a panel component in your page directory
2. In the page, call `setPanel({ content: <MyPanel />, title: 'Help' })`
3. Return `() => setPanel(null)` from the effect cleanup

### DrawerPanelOptions

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `ReactNode` | (required) | Panel body content |
| `title` | `string` | `"Info"` | Drawer header title |

### Integration Points

- `DrawerPanelProvider` wraps `SidebarProvider` in `layouts/RootLayout.tsx`
- `RightDrawer` wraps `SiteHeader` + `<Outlet />` in `RootLayout.tsx`
- `RightDrawerTrigger` is rendered in `site-header.tsx` after `ModeToggle`
- Provider auto-closes drawer and clears panel on `pathname` change
