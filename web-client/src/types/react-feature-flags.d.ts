declare module 'react-feature-flags' {
  import type { ReactNode } from 'react'

  interface Flag {
    name: string
    isActive: boolean
  }

  interface FlagsProviderProps {
    value: Flag[]
    children: ReactNode
  }

  interface FlagsProps {
    authorizedFlags: string[]
    exactFlags?: boolean
    renderOn?: (flags: Flag[]) => ReactNode
    renderOff?: () => ReactNode
    children?: ReactNode
  }

  export function FlagsProvider(props: FlagsProviderProps): JSX.Element
  export function Flags(props: FlagsProps): JSX.Element
}
