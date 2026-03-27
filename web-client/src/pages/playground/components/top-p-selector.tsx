import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'

interface TopPSelectorProps {
  value: number[]
  onValueChange: (value: number[]) => void
}

export function TopPSelector({ value, onValueChange }: TopPSelectorProps) {
  return (
    <div className="grid gap-2 pt-2">
      <HoverCard openDelay={200}>
        <HoverCardTrigger asChild>
          <div className="grid gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="top-p">Top P</Label>
              <span className="text-muted-foreground hover:border-border w-12 rounded-md border border-transparent px-2 py-0.5 text-right text-sm">
                {value}
              </span>
            </div>
            <Slider
              id="top-p"
              max={1}
              value={value}
              step={0.1}
              onValueChange={onValueChange}
              aria-label="Top P"
            />
          </div>
        </HoverCardTrigger>
        <HoverCardContent align="start" className="w-[260px] text-sm" side="left">
          Control diversity via nucleus sampling: 0.5 means half of all likelihood-weighted options
          are considered.
        </HoverCardContent>
      </HoverCard>
    </div>
  )
}
