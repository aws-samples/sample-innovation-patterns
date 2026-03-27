import { useVersionVersionGetQuery } from '@/services/api/generated'

interface VersionResponse {
  version?: string
  build?: string
}

export function VersionBadge() {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment -- generated API types
  const { data: apiVersion, error } = useVersionVersionGetQuery()
  const version = apiVersion as VersionResponse | undefined

  return (
    <div className="font-mono text-[10px] text-muted-foreground/50 space-y-0.5 px-2 pt-4 pb-2">
      <div>
        app: v{__APP_VERSION__} · {__BUILD_VERSION__}
      </div>
      {version && (
        <div className="opacity-70">
          api: v{version.version} · {version.build}
        </div>
      )}
      {error && <div className="opacity-50 text-destructive">api: offline</div>}
    </div>
  )
}
