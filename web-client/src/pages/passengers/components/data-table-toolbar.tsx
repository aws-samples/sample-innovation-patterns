import { type Table } from '@tanstack/react-table'
import { X } from 'lucide-react'
import { IconBolt, IconLoader2 } from '@tabler/icons-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

import {
  survivedOptions,
  classOptions,
  sexOptions,
  embarkedOptions,
  analysisOptions,
} from '../data/data'
import { DataTableFacetedFilter } from './data-table-faceted-filter'
import { DataTableViewOptions } from './data-table-view-options'

interface DataTableToolbarProps<TData> {
  table: Table<TData>
  onAnalyzeSelected?: () => void
  sqsAvailable: boolean
  bulkSubmitting?: boolean
}

export function DataTableToolbar<TData>({
  table,
  onAnalyzeSelected,
  sqsAvailable,
  bulkSubmitting = false,
}: DataTableToolbarProps<TData>) {
  const isFiltered = table.getState().columnFilters.length > 0
  const selectedCount = table.getFilteredSelectedRowModel().rows.length

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-1 items-center gap-2">
        <Input
          placeholder="Search passengers..."
          value={(table.getColumn('name')?.getFilterValue() as string) ?? ''}
          onChange={(event) => table.getColumn('name')?.setFilterValue(event.target.value)}
          className="h-8 w-[150px] lg:w-[250px]"
        />
        {table.getColumn('survived') && (
          <DataTableFacetedFilter
            column={table.getColumn('survived')}
            title="Survived"
            options={survivedOptions}
          />
        )}
        {table.getColumn('pclass') && (
          <DataTableFacetedFilter
            column={table.getColumn('pclass')}
            title="Class"
            options={classOptions}
          />
        )}
        {table.getColumn('sex') && (
          <DataTableFacetedFilter
            column={table.getColumn('sex')}
            title="Sex"
            options={sexOptions}
          />
        )}
        {table.getColumn('embarked') && (
          <DataTableFacetedFilter
            column={table.getColumn('embarked')}
            title="Embarked"
            options={embarkedOptions}
          />
        )}
        {table.getColumn('analysis') && (
          <DataTableFacetedFilter
            column={table.getColumn('analysis')}
            title="Analysis"
            options={analysisOptions}
          />
        )}
        {isFiltered && (
          <Button variant="ghost" size="sm" onClick={() => table.resetColumnFilters()}>
            Reset
            <X />
          </Button>
        )}
      </div>
      <div className="flex items-center gap-2">
        <DataTableViewOptions table={table} />
        {selectedCount > 0 && sqsAvailable && (
          <Button size="sm" onClick={onAnalyzeSelected} disabled={bulkSubmitting}>
            {bulkSubmitting ? (
              <IconLoader2 className="size-4 animate-spin" />
            ) : (
              <IconBolt className="size-4" />
            )}
            {bulkSubmitting ? 'Submitting…' : `Analyze ${selectedCount}`}
          </Button>
        )}
      </div>
    </div>
  )
}
