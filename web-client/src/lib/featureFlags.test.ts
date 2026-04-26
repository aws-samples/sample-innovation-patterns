// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { getFlags } from './featureFlags'

describe('getFlags', () => {
  it('converts config.features to Flag array', () => {
    const flags = getFlags()
    expect(flags).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'jobs', isActive: true }),
        expect.objectContaining({ name: 'chat', isActive: false }),
      ]),
    )
  })

  it('returns all feature keys from config', () => {
    const flags = getFlags()
    const names = flags.map((f) => f.name)
    expect(names).toContain('chat')
    expect(names).toContain('jobs')
    expect(names).toContain('playground')
    expect(names).toContain('kb_playground')
    expect(names).toContain('kitchen_sink')
  })

  it('returns objects with name and isActive properties', () => {
    const flags = getFlags()
    for (const flag of flags) {
      expect(flag).toHaveProperty('name')
      expect(flag).toHaveProperty('isActive')
      expect(typeof flag.name).toBe('string')
      expect(typeof flag.isActive).toBe('boolean')
    }
  })
})
