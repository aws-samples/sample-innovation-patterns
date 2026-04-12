// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { componentRegistry } from './component-registry'
import { ComponentWrapper } from './components/component-wrapper'

export function SinkIndexPage() {
  return (
    <div className="@container grid flex-1 gap-4 p-4">
      {Object.entries(componentRegistry)
        .filter(([, component]) => component.type === 'registry:ui')
        .map(([key, component]) => {
          const Demo = component.component
          return (
            <ComponentWrapper key={key} name={key} className={component.className || ''}>
              <Demo />
            </ComponentWrapper>
          )
        })}
    </div>
  )
}
