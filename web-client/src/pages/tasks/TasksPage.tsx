// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { z } from 'zod'

import { columns } from './components/columns'
import { DataTable } from './components/data-table'
import { taskSchema } from './data/schema'
import tasks from './data/tasks.json'

const data = z.array(taskSchema).parse(tasks)

export function TasksPage() {
  return (
    <div className="flex flex-1 flex-col gap-8 p-8">
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold tracking-tight">Welcome back!</h2>
          <p className="text-muted-foreground">Here&apos;s a list of your tasks for this month.</p>
        </div>
      </div>
      <DataTable data={data} columns={columns} />
    </div>
  )
}
