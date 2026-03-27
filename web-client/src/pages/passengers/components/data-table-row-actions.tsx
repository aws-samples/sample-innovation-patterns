import { type Row } from '@tanstack/react-table'
import { MoreHorizontal } from 'lucide-react'
import { useNavigate } from 'react-router'
import { IconBolt, IconEdit, IconTrash } from '@tabler/icons-react'

import { type TitanicPassengerResponse } from '@/services/api/generated'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { toast } from 'sonner'
import { useSubmitJobMutation } from '@/services/api/jobsApi'

interface DataTableRowActionsProps {
  row: Row<TitanicPassengerResponse>
  sqsAvailable?: boolean
  onSqsUnavailable?: () => void
}

export function DataTableRowActions({
  row,
  sqsAvailable = true,
  onSqsUnavailable,
}: DataTableRowActionsProps) {
  const navigate = useNavigate()
  const passenger = row.original
  const [submitJob] = useSubmitJobMutation()

  const handleAnalyze = async () => {
    if (!sqsAvailable) {
      onSqsUnavailable?.()
      return
    }
    const result = await submitJob({
      job_type: 'passenger_analysis',
      input_data: { ticket: passenger.ticket },
    })
    if ('data' in result && result.data) {
      void navigate('/jobs', { state: { newJobIds: [result.data.job_id] } })
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="data-[state=open]:bg-muted size-8">
          <MoreHorizontal />
          <span className="sr-only">Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[180px]">
        <DropdownMenuItem onClick={() => void handleAnalyze()}>
          <IconBolt className="size-4" />
          Analyze
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() =>
            void navigate(`/passengers/${encodeURIComponent(passenger.ticket)}?edit=true`)
          }
        >
          <IconEdit className="size-4" />
          Edit
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          variant="destructive"
          onClick={() => toast.warning('Delete is not yet implemented on the backend.')}
        >
          <IconTrash className="size-4" />
          Delete
          <DropdownMenuShortcut>⌘⌫</DropdownMenuShortcut>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
