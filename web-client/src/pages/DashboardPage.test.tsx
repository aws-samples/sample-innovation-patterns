// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { render, screen } from '@testing-library/react'
import { DrawerPanelContext, type DrawerPanelContextValue } from '@/components/drawer-panel-context'
import { DashboardPage } from './DashboardPage'

vi.mock('@/pages/dashboard/components/chart-area-interactive', () => ({
  ChartAreaInteractive: () => <div data-testid="chart">Chart</div>,
}))
vi.mock('@/pages/dashboard/components/data-table', () => ({
  DataTable: () => <div data-testid="data-table">Table</div>,
}))
vi.mock('@/pages/dashboard/components/section-cards', () => ({
  SectionCards: () => <div data-testid="section-cards">Cards</div>,
}))
vi.mock('@/pages/dashboard/DashboardHelpPanel', () => ({
  DashboardHelpPanel: () => <div>Help</div>,
}))

function renderDashboard() {
  const setPanel = vi.fn()
  const ctx: DrawerPanelContextValue = {
    panel: null,
    open: false,
    setOpen: vi.fn(),
    setPanel,
  }
  const result = render(
    <DrawerPanelContext.Provider value={ctx}>
      <DashboardPage />
    </DrawerPanelContext.Provider>,
  )
  return { ...result, setPanel }
}

describe('DashboardPage', () => {
  it('renders section cards, chart, and data table', () => {
    renderDashboard()
    expect(screen.getByTestId('section-cards')).toBeInTheDocument()
    expect(screen.getByTestId('chart')).toBeInTheDocument()
    expect(screen.getByTestId('data-table')).toBeInTheDocument()
  })

  it('sets the drawer panel on mount', () => {
    const { setPanel } = renderDashboard()
    expect(setPanel).toHaveBeenCalledWith(expect.objectContaining({ title: 'About This Panel' }))
  })
})
