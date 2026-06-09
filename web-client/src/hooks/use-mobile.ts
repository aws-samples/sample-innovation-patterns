// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import * as React from 'react'

const MOBILE_BREAKPOINT = 768
const MOBILE_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

function subscribe(onChange: () => void) {
  const mql = window.matchMedia(MOBILE_QUERY)
  mql.addEventListener('change', onChange)
  return () => mql.removeEventListener('change', onChange)
}

function getSnapshot() {
  return window.innerWidth < MOBILE_BREAKPOINT
}

export function useIsMobile() {
  // useSyncExternalStore is the idiomatic way to read from an external store
  // (matchMedia) — no effect, no synchronous setState. getServerSnapshot
  // returns false so SSR/initial render defaults to desktop.
  return React.useSyncExternalStore(subscribe, getSnapshot, () => false)
}
