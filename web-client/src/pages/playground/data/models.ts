// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
export const types = ['Amazon Nova', 'Anthropic Claude'] as const

export type ModelType = (typeof types)[number]

export interface Model<Type = string> {
  id: string
  name: string
  description: string
  strengths?: string
  type: Type
}

export const models: Model<ModelType>[] = [
  {
    id: 'amazon.nova-pro-v1:0',
    name: 'Amazon Nova Pro',
    description:
      'High-capability model for complex tasks including analysis, coding, and creative content.',
    type: 'Amazon Nova',
    strengths: 'Complex reasoning, multi-step tasks, long-form content',
  },
  {
    id: 'amazon.nova-2-lite-v1:0',
    name: 'Amazon Nova 2 Lite',
    description: 'Fast, cost-effective model for general tasks.',
    type: 'Amazon Nova',
    strengths: 'Speed, cost efficiency, straightforward tasks',
  },
  {
    id: 'us.anthropic.claude-opus-4-6-v1',
    name: 'Claude Opus 4.6',
    description: 'Most capable Claude model for complex reasoning and analysis.',
    type: 'Anthropic Claude',
    strengths: 'Deep reasoning, complex analysis, nuanced writing',
  },
  {
    id: 'us.anthropic.claude-sonnet-4-6',
    name: 'Claude Sonnet 4.6',
    description: 'Balanced performance and cost for most tasks.',
    type: 'Anthropic Claude',
    strengths: 'Coding, analysis, creative writing, instruction following',
  },
  {
    id: 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    name: 'Claude Haiku 4.5',
    description: 'Fast, compact model optimized for speed and cost efficiency.',
    type: 'Anthropic Claude',
    strengths: 'Low latency, cost efficiency, straightforward tasks',
  },
]
