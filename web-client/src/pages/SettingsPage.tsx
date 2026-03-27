import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'

import { config } from '@/lib/config'

export function SettingsPage() {
  const entries = Object.entries(config)

  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="text-muted-foreground">Settings page placeholder.</p>

      <Separator />

      <div className="flex flex-col gap-3">
        <div>
          <h2 className="text-lg font-semibold">Runtime Configuration</h2>
          <p className="text-muted-foreground text-sm">
            Values from{' '}
            <code className="bg-muted rounded px-1 py-0.5 text-xs">window.__CONFIG__</code> injected
            at deploy time.
          </p>
        </div>
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader className="bg-muted">
              <TableRow>
                <TableHead>Key</TableHead>
                <TableHead>Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.length > 0 ? (
                entries.map(([key, value]) => (
                  <TableRow key={key}>
                    <TableCell className="font-medium">
                      <code className="text-xs">{key}</code>
                    </TableCell>
                    <TableCell>
                      {value ? (
                        <code className="text-muted-foreground text-xs break-all">
                          {String(value)}
                        </code>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          empty
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={2} className="h-16 text-center text-muted-foreground">
                    No runtime configuration found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}
