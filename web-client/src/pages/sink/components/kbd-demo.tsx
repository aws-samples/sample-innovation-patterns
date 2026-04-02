import { ArrowLeftIcon, ArrowRightIcon, CommandIcon, WavesIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ButtonGroup } from '@/components/ui/button-group'
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group'
import { Kbd, KbdGroup } from '@/components/ui/kbd'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function KbdDemo() {
  return (
    <div className="flex max-w-xs flex-col items-start gap-4">
      <div className="flex items-center gap-2">
        <Kbd>Ctrl</Kbd>
        <Kbd>⌘K</Kbd>
        <Kbd>Ctrl + B</Kbd>
      </div>
      <div className="flex items-center gap-2">
        <Kbd>⌘</Kbd>
        <Kbd>C</Kbd>
      </div>
      <KbdGroup>
        <Kbd>Ctrl</Kbd>
        <Kbd>Shift</Kbd>
        <Kbd>P</Kbd>
      </KbdGroup>
      <div className="flex items-center gap-2">
        <Kbd>↑</Kbd>
        <Kbd>↓</Kbd>
        <Kbd>←</Kbd>
        <Kbd>→</Kbd>
      </div>
      <KbdGroup>
        <Kbd>
          <CommandIcon />
        </Kbd>
        <Kbd>
          <ArrowLeftIcon />
        </Kbd>
        <Kbd>
          <ArrowRightIcon />
        </Kbd>
      </KbdGroup>
      <KbdGroup>
        <Kbd>
          <ArrowLeftIcon />
          Left
        </Kbd>
        <Kbd>
          <WavesIcon />
          Voice Enabled
        </Kbd>
      </KbdGroup>
      <InputGroup>
        <InputGroupInput />
        <InputGroupAddon>
          <Kbd>Space</Kbd>
        </InputGroupAddon>
      </InputGroup>
      <ButtonGroup>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="sm" variant="outline">
              Save
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <div className="flex items-center gap-2">
              Save Changes <Kbd>S</Kbd>
            </div>
          </TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button size="sm" variant="outline">
              Print
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <div className="flex items-center gap-2">
              Print Document{' '}
              <KbdGroup>
                <Kbd>Ctrl</Kbd>
                <Kbd>P</Kbd>
              </KbdGroup>
            </div>
          </TooltipContent>
        </Tooltip>
      </ButtonGroup>
      <Kbd>
        <samp>File</samp>
      </Kbd>
    </div>
  )
}
