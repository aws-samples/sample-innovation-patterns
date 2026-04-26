// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { Navigate, useParams } from 'react-router'
import { componentRegistry } from './component-registry'

export function SinkDetailPage() {
  const { name } = useParams<{ name: string }>()
  const component = componentRegistry[name as keyof typeof componentRegistry]

  if (!component) return <Navigate to="/sink" replace />

  const Demo = component.component
  const isPage = component.type === 'registry:page'

  return (
    <div className={isPage ? undefined : 'p-6'}>
      <Demo />
    </div>
  )
}
