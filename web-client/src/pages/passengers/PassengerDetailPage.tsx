import * as React from 'react'
import { useParams, useSearchParams, useNavigate, Link } from 'react-router'
import { IconArrowLeft, IconBolt, IconEdit, IconDeviceFloppy } from '@tabler/icons-react'

import {
  useGetPassengerApiV1PassengersTicketGetQuery,
  useUpdatePassengerApiV1PassengersTicketPutMutation,
} from '@/services/api/generated'
import { useSubmitJobMutation } from '@/services/api/jobsApi'
import { useListJobsQuery } from '@/services/api/jobsApi'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import { toast } from 'sonner'
import { PassengerForm } from './components/PassengerForm'
import type { PassengerFormData } from '@/schemas/passenger'

type Analysis = {
  survival_assessment?: string
  risk_factors?: string[]
  historical_context?: string
  confidence?: string
}

function FieldView({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm">{value ?? '—'}</p>
    </div>
  )
}

export function PassengerDetailPage() {
  const { ticket } = useParams<{ ticket: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const startEditing = searchParams.get('edit') === 'true'

  const {
    data: passenger,
    isLoading,
    error,
  } = useGetPassengerApiV1PassengersTicketGetQuery(
    { ticket: ticket! },
    { skip: !ticket, refetchOnMountOrArgChange: true },
  )
  const [updatePassenger, { isLoading: isSaving }] =
    useUpdatePassengerApiV1PassengersTicketPutMutation()
  const [submitJob] = useSubmitJobMutation()
  const { isError: sqsUnavailable } = useListJobsQuery({ limit: 1 })

  const [editing, setEditing] = React.useState(startEditing)

  const handleSave = async (data: PassengerFormData) => {
    if (!ticket) return
    const result = await updatePassenger({
      ticket,
      titanicPassengerCreate: {
        ...data,
        ticket,
      },
    })
    if ('data' in result) {
      toast.success('Passenger updated')
      setEditing(false)
    }
  }

  const handleAnalyze = async () => {
    if (!ticket || sqsUnavailable) return
    try {
      const result = await submitJob({
        job_type: 'passenger_analysis',
        input_data: { ticket },
      }).unwrap()
      void navigate('/jobs', { state: { newJobIds: [result.job_id] } })
    } catch {
      toast.error('Failed to submit analysis job')
    }
  }

  if (isLoading) return <p className="p-8 text-muted-foreground">Loading…</p>
  if (error || !passenger) return <p className="p-8 text-destructive">Passenger not found.</p>

  const analysis = passenger.analysis as Analysis | null

  const formDefaults: PassengerFormData = {
    ticket: passenger.ticket,
    name: passenger.name,
    pclass: passenger.pclass,
    survived: passenger.survived,
    sex: passenger.sex as 'male' | 'female',
    age: passenger.age ?? null,
    sibsp: passenger.sibsp,
    parch: passenger.parch,
    fare: passenger.fare ?? null,
    cabin: passenger.cabin ?? null,
    embarked: (passenger.embarked as 'C' | 'Q' | 'S') ?? null,
    boat: passenger.boat ?? null,
    body: passenger.body ?? null,
    home_dest: passenger.home_dest ?? null,
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/passengers">Passengers</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{ticket}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => void navigate('/passengers')}>
            <IconArrowLeft className="size-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold">{passenger.name}</h1>
            <p className="text-sm text-muted-foreground font-mono">Ticket {ticket}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {!sqsUnavailable && (
            <Button variant="outline" size="sm" onClick={() => void handleAnalyze()}>
              <IconBolt className="size-4" />
              {analysis ? 'Re-analyze' : 'Analyze'}
            </Button>
          )}
          {editing ? (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditing(false)}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button type="submit" form="passenger-form" size="sm" disabled={isSaving}>
                <IconDeviceFloppy className="size-4" />
                Save
              </Button>
            </>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
              <IconEdit className="size-4" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Passenger Details</CardTitle>
          </CardHeader>
          <CardContent>
            {editing ? (
              <PassengerForm
                formId="passenger-form"
                defaultValues={formDefaults}
                onSubmit={handleSave}
              />
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <FieldView label="Name" value={passenger.name} />
                <FieldView
                  label="Class"
                  value={passenger.pclass === 1 ? '1st' : passenger.pclass === 2 ? '2nd' : '3rd'}
                />
                <FieldView label="Survived" value={passenger.survived ? 'Yes' : 'No'} />
                <FieldView label="Sex" value={passenger.sex} />
                <FieldView label="Age" value={passenger.age} />
                <FieldView label="SibSp" value={passenger.sibsp} />
                <FieldView label="Parch" value={passenger.parch} />
                <FieldView label="Fare" value={passenger.fare} />
                <FieldView label="Cabin" value={passenger.cabin} />
                <FieldView label="Embarked" value={passenger.embarked} />
                <FieldView label="Boat" value={passenger.boat} />
                <FieldView label="Body" value={passenger.body} />
                <FieldView label="Home/Destination" value={passenger.home_dest} />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {analysis ? (
              <div className="space-y-4">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <Badge
                    variant="outline"
                    className={
                      analysis.confidence === 'HIGH'
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600'
                        : analysis.confidence === 'MEDIUM'
                          ? 'border-amber-500/30 bg-amber-500/10 text-amber-600'
                          : 'border-red-500/30 bg-red-500/10 text-red-600'
                    }
                  >
                    {analysis.confidence}
                  </Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Survival Assessment</p>
                  <p className="text-sm">{analysis.survival_assessment}</p>
                </div>
                {analysis.risk_factors && analysis.risk_factors.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Risk Factors</p>
                    <ul className="text-sm list-disc list-inside space-y-0.5">
                      {analysis.risk_factors.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Historical Context</p>
                  <p className="text-sm">{analysis.historical_context}</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <p className="text-sm text-muted-foreground">No analysis yet.</p>
                {!sqsUnavailable && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => void handleAnalyze()}
                  >
                    <IconBolt className="size-4" />
                    Analyze
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
