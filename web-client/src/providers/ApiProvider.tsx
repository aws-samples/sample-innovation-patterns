// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import type { ReactNode } from 'react'
import { Provider } from 'react-redux'
import { store } from '@/store/store'

export function ApiProvider({ children }: { children: ReactNode }) {
  return <Provider store={store}>{children}</Provider>
}
