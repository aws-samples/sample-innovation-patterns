// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { config } from '@/lib/config'

interface Flag {
  name: string
  isActive: boolean
}

/** Convert the features config object to the array format react-feature-flags expects. */
export function getFlags(): Flag[] {
  return (Object.keys(config.features) as Array<keyof typeof config.features>).map((name) => ({
    name,
    isActive: config.features[name],
  }))
}
