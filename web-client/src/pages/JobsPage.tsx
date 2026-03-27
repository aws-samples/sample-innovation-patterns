import * as React from 'react'
import { Link, useLocation } from 'react-router'
import {
  IconCheck,
  IconClock,
  IconLoader2,
  IconAlertTriangle,
  IconRefresh,
  IconChevronLeft,
  IconChevronRight,
  IconChevronsLeft,
  IconChevronsRight,
} from '@tabler/icons-react'

import { useListJobsQuery, useGetJobQuery, type JobResponse } from '@/services/api/jobsApi'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { getResultAction } from '@/config/jobTypeRegistry'

const STATUS_CONFIG = {
  PENDING: {
    icon: IconClock,
    label: 'Queued',
    className: 'bg-amber-500/15 text-amber-600 border-amber-500/30',
    animate: false,
  },
  PROCESSING: {
    icon: IconLoader2,
    label: 'Processing',
    className: 'bg-blue-500/15 text-blue-600 border-blue-500/30',
    animate: true,
  },
  COMPLETED: {
    icon: IconCheck,
    label: 'Complete',
    className: 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30',
    animate: false,
  },
  FAILED: {
    icon: IconAlertTriangle,
    label: 'Failed',
    className: 'bg-red-500/15 text-red-600 border-red-500/30',
    animate: false,
  },
} as const

function StatusBadge({ status }: { status: keyof typeof STATUS_CONFIG }) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  return (
    <Badge variant="outline" className={`gap-1.5 ${config.className}`}>
      <Icon className={`size-3.5 ${config.animate ? 'animate-spin' : ''}`} />
      {config.label}
    </Badge>
  )
}

function TimeAgo({ iso }: { iso: string }) {
  const [now, setNow] = React.useState(() => Date.now())
  React.useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  const seconds = Math.floor((now - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return <span>{seconds}s ago</span>
  if (seconds < 3600) return <span>{Math.floor(seconds / 60)}m ago</span>
  return <span>{Math.floor(seconds / 3600)}h ago</span>
}

function JobRow({ job, isNew }: { job: JobResponse; isNew?: boolean }) {
  const { data: liveJob } = useGetJobQuery(job.job_id, {
    skip: job.status === 'COMPLETED' || job.status === 'FAILED',
  })
  const current = liveJob ?? job
  const resultAction =
    current.status === 'COMPLETED'
      ? getResultAction(current.job_type, current.metadata ?? current.input_data)
      : null

  return (
    <div
      className={`border rounded-lg transition-all duration-200 hover:border-foreground/20 ${isNew ? 'ring-2 ring-primary/50' : ''}`}
    >
      <div className="flex items-center gap-4 p-4">
        <StatusBadge status={current.status} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-mono truncate">{current.job_id.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">{current.job_type}</p>
        </div>
        {resultAction && (
          <Link to={resultAction.href}>
            <Badge variant="secondary" className="text-xs cursor-pointer hover:bg-secondary/80">
              {resultAction.label} →
            </Badge>
          </Link>
        )}
        <div className="text-xs text-muted-foreground">
          <TimeAgo iso={current.created_at} />
        </div>
      </div>
      {current.status === 'FAILED' && current.error && (
        <div className="px-4 pb-4">
          <Separator className="mb-3" />
          <p className="text-sm text-red-600 font-mono">{current.error}</p>
        </div>
      )}
    </div>
  )
}

const PAGE_SIZES = [10, 20, 25, 50]

export function JobsPage() {
  const { data: jobs, isLoading, isError, isFetching, refetch } = useListJobsQuery({ limit: 200 })
  const [statusFilter, setStatusFilter] = React.useState<string | null>(null)
  const [page, setPage] = React.useState(0)
  const [pageSize, setPageSize] = React.useState(20)
  const location = useLocation()
  const newJobIds = (location.state as { newJobIds?: string[] } | null)?.newJobIds ?? []

  const sorted = React.useMemo(() => {
    if (!jobs) return []
    const s = [...jobs].sort((a, b) => b.created_at.localeCompare(a.created_at))
    return statusFilter ? s.filter((j) => j.status === statusFilter) : s
  }, [jobs, statusFilter])

  // Reset to first page when filter changes
  React.useEffect(() => setPage(0), [statusFilter])

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize)

  const counts = React.useMemo(() => {
    if (!jobs) return { PENDING: 0, PROCESSING: 0, COMPLETED: 0, FAILED: 0 }
    return jobs.reduce((acc, j) => ({ ...acc, [j.status]: (acc[j.status] ?? 0) + 1 }), {
      PENDING: 0,
      PROCESSING: 0,
      COMPLETED: 0,
      FAILED: 0,
    })
  }, [jobs])

  if (isError) {
    return (
      <div className="flex flex-1 flex-col p-8">
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <IconAlertTriangle className="size-8 text-muted-foreground mb-3" />
            <p className="text-sm font-medium">Background processing not available</p>
            <p className="text-xs text-muted-foreground mt-1">
              Deploy the SQS pattern in this namespace to enable job processing.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Jobs</h1>
          <p className="text-sm text-muted-foreground">
            Track background job progress in real time.
          </p>
        </div>
        <Button variant="outline" size="icon" onClick={() => void refetch()} disabled={isFetching}>
          <IconRefresh className={`size-4 ${isFetching ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {([null, 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'] as const).map((s) => (
          <Button
            key={s ?? 'all'}
            variant={statusFilter === s ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(s)}
          >
            {s ? STATUS_CONFIG[s].label : 'All'}
            <Badge variant="secondary" className="ml-1.5 text-xs">
              {s ? counts[s] : (jobs?.length ?? 0)}
            </Badge>
          </Button>
        ))}
      </div>

      <div className="space-y-2">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <IconLoader2 className="size-5 animate-spin text-muted-foreground" />
          </div>
        )}
        {jobs?.length === 0 && !isLoading && (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-8 text-center">
              <p className="text-sm text-muted-foreground">
                No jobs yet. Submit analysis from the Passengers page.
              </p>
            </CardContent>
          </Card>
        )}
        {paged.map((job) => (
          <JobRow key={job.job_id} job={job} isNew={newJobIds.includes(job.job_id)} />
        ))}
      </div>

      {/* Pagination */}
      {sorted.length > 0 && (
        <div className="flex items-center justify-between px-2">
          <p className="text-sm text-muted-foreground">
            {sorted.length} job{sorted.length !== 1 ? 's' : ''}
          </p>
          <div className="flex items-center gap-6 lg:gap-8">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium">Per page</p>
              <Select
                value={String(pageSize)}
                onValueChange={(v) => {
                  setPageSize(Number(v))
                  setPage(0)
                }}
              >
                <SelectTrigger className="h-8 w-[70px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent side="top">
                  {PAGE_SIZES.map((s) => (
                    <SelectItem key={s} value={String(s)}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-sm font-medium w-[100px] text-center">
              Page {page + 1} of {pageCount}
            </p>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className="size-8 hidden lg:flex"
                onClick={() => setPage(0)}
                disabled={page === 0}
              >
                <IconChevronsLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="size-8"
                onClick={() => setPage(page - 1)}
                disabled={page === 0}
              >
                <IconChevronLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="size-8"
                onClick={() => setPage(page + 1)}
                disabled={page >= pageCount - 1}
              >
                <IconChevronRight className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="size-8 hidden lg:flex"
                onClick={() => setPage(pageCount - 1)}
                disabled={page >= pageCount - 1}
              >
                <IconChevronsRight className="size-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
