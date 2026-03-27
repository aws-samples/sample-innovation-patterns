export interface ResultAction {
  label: string
  href: string
}

export type ResultActionBuilder = (metadata: Record<string, unknown>) => ResultAction

const JOB_TYPE_REGISTRY: Record<string, ResultActionBuilder> = {
  passenger_analysis: (metadata) => ({
    label: `View Passenger ${String(metadata.ticket)}`,
    href: `/passengers/${encodeURIComponent(String(metadata.ticket))}`,
  }),
}

export function getResultAction(
  jobType: string,
  metadata: Record<string, unknown> | null,
): ResultAction | null {
  if (!metadata) return null
  const builder = JOB_TYPE_REGISTRY[jobType]
  return builder ? builder(metadata) : null
}
