export interface KBModel {
  id: string
  name: string
}

export const kbModels: KBModel[] = [
  { id: 'amazon.nova-pro-v1:0', name: 'Amazon Nova Pro' },
  { id: 'amazon.nova-2-lite-v1:0', name: 'Amazon Nova 2 Lite' },
  { id: 'us.anthropic.claude-sonnet-4-6', name: 'Claude Sonnet 4.6' },
  { id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0', name: 'Claude Haiku 4.5' },
  { id: 'us.anthropic.claude-opus-4-6-v1', name: 'Claude Opus 4.6' },
]

export const defaultKBModel = kbModels[0]
