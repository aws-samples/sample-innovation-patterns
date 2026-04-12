// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { type ColumnDef } from '@tanstack/react-table'
import { type TitanicPassengerResponse } from '@/services/api/generated'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { DataTableColumnHeader } from './data-table-column-header'
import { DataTableRowActions } from './data-table-row-actions'

export const columns: ColumnDef<TitanicPassengerResponse>[] = [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && 'indeterminate')
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
        className="translate-y-[2px]"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
        className="translate-y-[2px]"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'ticket',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Ticket" />,
    cell: ({ row }) => <div className="w-[80px] font-mono">{row.getValue('ticket')}</div>,
    enableHiding: false,
  },
  {
    accessorKey: 'name',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
    cell: ({ row }) => (
      <span className="max-w-[200px] truncate font-medium">{row.getValue('name')}</span>
    ),
  },
  {
    accessorKey: 'pclass',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Class" />,
    cell: ({ row }) => {
      const v = row.getValue('pclass')
      return (
        <Badge variant="outline" className="text-muted-foreground px-1.5">
          {v === 1 ? '1st' : v === 2 ? '2nd' : '3rd'}
        </Badge>
      )
    },
    filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
  },
  {
    accessorKey: 'survived',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Survived" />,
    cell: ({ row }) => {
      const v = row.getValue('survived')
      return (
        <Badge
          variant="outline"
          className={
            v
              ? 'border-green-500/30 bg-green-500/10 text-green-600'
              : 'border-red-500/30 bg-red-500/10 text-red-600'
          }
        >
          {v ? 'Yes' : 'No'}
        </Badge>
      )
    },
    filterFn: (row, id, value: string[]) => value.includes(String(row.getValue(id))),
  },
  {
    accessorKey: 'sex',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Sex" />,
    cell: ({ row }) => (
      <Badge variant="outline" className="text-muted-foreground px-1.5">
        {row.getValue('sex')}
      </Badge>
    ),
    filterFn: (row, id, value: string[]) => value.includes(row.getValue(id)),
  },
  {
    accessorKey: 'age',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Age" className="text-right" />
    ),
    cell: ({ row }) => <div className="text-right">{row.getValue('age') ?? '—'}</div>,
  },
  {
    accessorKey: 'embarked',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Embarked" />,
    cell: ({ row }) => (
      <Badge variant="outline" className="text-muted-foreground px-1.5">
        {row.getValue('embarked') ?? '—'}
      </Badge>
    ),
    filterFn: (row, id, value: string[]) => value.includes(row.getValue(id)),
  },
  {
    id: 'analysis',
    accessorFn: (row) => (row.analysis ? 'analyzed' : 'pending'),
    header: ({ column }) => <DataTableColumnHeader column={column} title="Analysis" />,
    cell: ({ row }) => {
      const analysis = row.original.analysis as { confidence?: string } | null
      if (!analysis) return <span className="text-muted-foreground text-xs">—</span>
      const c = analysis.confidence
      const cls =
        c === 'HIGH'
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600'
          : c === 'MEDIUM'
            ? 'border-amber-500/30 bg-amber-500/10 text-amber-600'
            : 'border-red-500/30 bg-red-500/10 text-red-600'
      return (
        <Badge variant="outline" className={cls}>
          {c}
        </Badge>
      )
    },
    filterFn: (row, id, value: string[]) => value.includes(row.getValue(id)),
  },
  {
    id: 'actions',
    cell: ({ row, table }) => {
      const meta = table.options.meta as {
        sqsAvailable?: boolean
        onSqsUnavailable?: () => void
      }
      return (
        <DataTableRowActions
          row={row}
          sqsAvailable={meta?.sqsAvailable}
          onSqsUnavailable={meta?.onSqsUnavailable}
        />
      )
    },
  },
]
