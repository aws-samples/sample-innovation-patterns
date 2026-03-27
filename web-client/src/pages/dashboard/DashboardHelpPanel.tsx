export function DashboardHelpPanel() {
  return (
    <div className="space-y-4 text-sm">
      <p>
        This is the <strong>Right Drawer</strong> — a route-specific help panel that any page can
        opt into.
      </p>
      <h4 className="font-medium">How it works</h4>
      <p>
        Pages register panel content using the{' '}
        <code className="bg-muted rounded px-1 py-0.5">useDrawerPanel()</code> hook from{' '}
        <code className="bg-muted rounded px-1 py-0.5">drawer-panel-provider.tsx</code>. The icon in
        the header appears automatically when a panel is registered.
      </p>
      <h4 className="font-medium">Add a panel to your page</h4>
      <ol className="list-decimal space-y-1 pl-4">
        <li>Create a panel component in your page directory</li>
        <li>
          Call{' '}
          <code className="bg-muted rounded px-1 py-0.5">setPanel({'{ content, title }'})</code> in
          a <code className="bg-muted rounded px-1 py-0.5">useEffect</code>
        </li>
        <li>
          Return <code className="bg-muted rounded px-1 py-0.5">() =&gt; setPanel(null)</code> from
          the cleanup
        </li>
      </ol>
    </div>
  )
}
