import { useEffect } from 'react'
import { ChartAreaInteractive } from '@/pages/dashboard/components/chart-area-interactive'
import { DataTable } from '@/pages/dashboard/components/data-table'
import { SectionCards } from '@/pages/dashboard/components/section-cards'
import { useDrawerPanel } from '@/hooks/use-drawer-panel'
import { DashboardHelpPanel } from '@/pages/dashboard/DashboardHelpPanel'
import data from '@/pages/dashboard/data.json'

export function DashboardPage() {
  const { setPanel } = useDrawerPanel()

  useEffect(() => {
    setPanel({
      content: <DashboardHelpPanel />,
      title: 'About This Panel',
    })
    return () => setPanel(null)
  }, [setPanel])

  return (
    <div className="@container/main flex flex-1 flex-col gap-2">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <SectionCards />
        <div className="px-4 lg:px-6">
          <ChartAreaInteractive />
        </div>
        <DataTable data={data} />
      </div>
    </div>
  )
}
