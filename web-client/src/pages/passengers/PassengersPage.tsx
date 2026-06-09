// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import * as React from 'react'
import { useNavigate } from 'react-router'

import { useListPassengersApiV1PassengersGetQuery } from '@/services/api/generated'
import { type TitanicPassengerResponse } from '@/services/api/generated'
import { useListJobsQuery, useSubmitJobMutation } from '@/services/api/jobsApi'

import { columns } from './components/columns'
import { DataTable } from './components/data-table'
import { SqsUnavailableDialog } from './components/sqs-unavailable-dialog'

export function PassengersPage() {
  const navigate = useNavigate()
  const {
    data: passengers,
    isLoading,
    error,
  } = useListPassengersApiV1PassengersGetQuery({ limit: 500 })
  const { isError: sqsUnavailable } = useListJobsQuery({ limit: 1 })
  const [showSqsDialog, setShowSqsDialog] = React.useState(false)
  const [submitJob] = useSubmitJobMutation()
  const [bulkSubmitting, setBulkSubmitting] = React.useState(false)
  const [bulkProgress, setBulkProgress] = React.useState({ done: 0, total: 0 })

  const handleAnalyzeSelected = async (rows: TitanicPassengerResponse[]) => {
    if (sqsUnavailable) {
      setShowSqsDialog(true)
      return
    }
    setBulkSubmitting(true)
    setBulkProgress({ done: 0, total: rows.length })
    const jobIds: string[] = []
    for (const p of rows) {
      const result = await submitJob({
        job_type: 'passenger_analysis',
        input_data: { ticket: p.ticket },
      })
      if ('data' in result && result.data) jobIds.push(result.data.job_id)
      setBulkProgress((prev) => ({ ...prev, done: prev.done + 1 }))
    }
    setBulkSubmitting(false)
    if (jobIds.length) void navigate('/jobs', { state: { newJobIds: jobIds } })
  }

  const handleRowClick = (row: TitanicPassengerResponse) => {
    void navigate(`/passengers/${encodeURIComponent(row.ticket)}`)
  }

  return (
    <div className="flex flex-1 flex-col gap-8 p-8">
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold tracking-tight">Titanic Passengers</h2>
          <p className="text-muted-foreground">Browse, search, and analyze passenger records.</p>
        </div>
      </div>
      {isLoading && <p className="text-muted-foreground">Loading…</p>}
      {error && <p className="text-destructive">Failed to load passengers.</p>}
      {passengers && (
        <DataTable
          data={passengers}
          columns={columns}
          sqsAvailable={!sqsUnavailable}
          onAnalyzeSelected={(rows) => void handleAnalyzeSelected(rows)}
          onSqsUnavailable={() => setShowSqsDialog(true)}
          bulkSubmitting={bulkSubmitting}
          bulkProgress={bulkProgress}
          onRowClick={(row) => handleRowClick(row)}
        />
      )}
      <SqsUnavailableDialog open={showSqsDialog} onClose={() => setShowSqsDialog(false)} />
    </div>
  )
}
