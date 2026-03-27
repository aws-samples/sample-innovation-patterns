import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface SqsUnavailableDialogProps {
  open: boolean
  onClose: () => void
}

export function SqsUnavailableDialog({ open, onClose }: SqsUnavailableDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Background Processing Not Available</DialogTitle>
          <DialogDescription>
            The SQS background processing pattern is not deployed in this environment. Deploy it to
            enable passenger analysis.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={onClose}>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
