# components/

Shared layout and UI components. For shadcn/ui primitives, see `ui/AGENTS.md`.

- Right drawer panel: pages register via `useDrawerPanel()` from `drawer-panel-provider.tsx` — requires `useEffect` with cleanup `() => setPanel(null)`
- `RightDrawerTrigger` must be a descendant of `<RightDrawer>` (vaul constraint) — both live in `RootLayout`
- `DrawerPanelProvider` auto-clears panel on route change — pages don't need to coordinate close behavior

See README.md for component inventory and integration points.
