import { useRef, useState } from 'react'
import { Square } from 'lucide-react'
import { IconAlertTriangle } from '@tabler/icons-react'
import { OidcClient } from '@axa-fr/oidc-client'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { MarkdownContent } from '@/components/markdown-content'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Slider } from '@/components/ui/slider'
import { Textarea } from '@/components/ui/textarea'
import { API_BASE_URL } from '@/services/api/baseApi'

import { kbModels, defaultKBModel } from './data/kb-models'

export function KBPlaygroundPage() {
  const [modelId, setModelId] = useState(defaultKBModel.id)
  const [numResults, setNumResults] = useState([5])
  const [filterJson, setFilterJson] = useState('')
  const [filterError, setFilterError] = useState('')
  const [query, setQuery] = useState('')
  const [output, setOutput] = useState('')
  const [citations, setCitations] = useState<unknown[] | null>(null)
  const [showCitations, setShowCitations] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [unavailable, setUnavailable] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  async function handleSubmit() {
    if (!query.trim()) return

    let filter: Record<string, unknown> | null = null
    if (filterJson.trim()) {
      try {
        filter = JSON.parse(filterJson) as Record<string, unknown>
      } catch {
        setFilterError('Invalid JSON')
        return
      }
    }

    setIsStreaming(true)
    setOutput('')
    setCitations(null)
    setError(null)
    setFilterError('')
    setUnavailable(false)
    const controller = new AbortController()
    abortControllerRef.current = controller

    let token: string | undefined
    try {
      token = OidcClient.get()?.tokens?.idToken
    } catch {
      /* auth disabled */
    }

    try {
      // eslint-disable-next-line no-restricted-globals -- SSE streaming requires raw fetch
      const response = await fetch(`${API_BASE_URL}/api/v1/sse/kb/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query,
          model_id: modelId,
          num_results: numResults[0],
          filter,
        }),
        signal: controller.signal,
      })

      if (response.status === 503) {
        const body = (await response.json()) as { detail?: string }
        setError(body.detail ?? 'Knowledge Base not configured')
        setUnavailable(true)
        return
      }

      if (!response.ok) {
        setError(`Error: ${response.status} — ${await response.text()}`)
        return
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (!line.startsWith('data: ') || line === 'data: [DONE]') continue
          const data = JSON.parse(line.slice(6)) as {
            text?: string
            citations?: unknown[]
            error?: string
          }
          if (data.text) {
            fullText += data.text
            setOutput(fullText)
          }
          if (data.citations) {
            setCitations(data.citations)
          }
          if (data.error) {
            setError(data.error)
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') setError(`Error: ${(err as Error).message}`)
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  function handleCancel() {
    abortControllerRef.current?.abort()
  }

  if (unavailable) {
    return (
      <div className="flex flex-1 flex-col">
        <div className="flex items-center gap-2 px-4 py-4 md:h-16">
          <h2 className="pl-4 text-lg font-semibold">KB Playground</h2>
        </div>
        <Separator />
        <div className="flex flex-1 items-start justify-center p-8">
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <IconAlertTriangle className="size-8 text-muted-foreground mb-3" />
              <p className="text-sm font-medium">Knowledge Base not available</p>
              <p className="text-xs text-muted-foreground mt-1">
                Deploy the Bedrock KB pattern in this namespace to enable knowledge base search.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center gap-2 px-4 py-4 md:h-16">
        <h2 className="pl-4 text-lg font-semibold">KB Playground</h2>
      </div>
      <Separator />
      <div className="min-h-0 flex-1 overflow-hidden px-4 py-6">
        <div className="grid h-full gap-6 md:grid-cols-[1fr_200px]">
          {/* Controls — right column */}
          <div className="hidden flex-col gap-6 overflow-y-auto sm:flex md:order-2">
            <div className="grid gap-2">
              <Label>Model</Label>
              <Select value={modelId} onValueChange={setModelId}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {kbModels.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-3">
              <Label>Results: {numResults[0]}</Label>
              <Slider value={numResults} onValueChange={setNumResults} min={1} max={20} step={1} />
            </div>

            <div className="grid gap-2">
              <Label>Metadata Filter (JSON)</Label>
              <Textarea
                placeholder='{"equals": {"key": "pclass", "value": 1}}'
                className="min-h-[80px] resize-none font-mono text-xs"
                value={filterJson}
                onChange={(e) => {
                  setFilterJson(e.target.value)
                  setFilterError('')
                }}
              />
              {filterError && <p className="text-xs text-red-500">{filterError}</p>}
              <p className="text-xs text-muted-foreground">
                Optional. Example: {`{"equals": {"key": "pclass", "value": 1}}`}
              </p>
            </div>

            <Separator />

            <div className="flex items-center gap-2">
              {isStreaming ? (
                <Button variant="destructive" className="w-full" onClick={handleCancel}>
                  <Square className="mr-2 h-4 w-4" />
                  Stop
                </Button>
              ) : (
                <Button
                  className="w-full"
                  onClick={() => void handleSubmit()}
                  disabled={!query.trim()}
                >
                  Search
                </Button>
              )}
            </div>
          </div>

          {/* Query + Output — left column */}
          <div className="flex min-h-0 flex-1 flex-col gap-4 md:order-1">
            <div className="grid min-h-0 flex-1 grid-rows-[1fr_1fr] gap-6 lg:grid-cols-[1fr_1fr] lg:grid-rows-[1fr]">
              <Textarea
                placeholder="Tell me about first class passengers..."
                className="min-h-0 resize-none overflow-auto p-4"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <div className="flex min-h-0 flex-col gap-2 overflow-hidden">
                <div className="bg-muted relative min-h-0 flex-1 overflow-auto rounded-md border p-4">
                  {output ? (
                    <div>
                      <MarkdownContent className="prose prose-sm dark:prose-invert max-w-none">
                        {output}
                      </MarkdownContent>
                      {isStreaming && (
                        <span className="animate-pulse text-muted-foreground">▊</span>
                      )}
                    </div>
                  ) : (
                    !isStreaming && (
                      <p className="text-muted-foreground text-sm">Output will appear here...</p>
                    )
                  )}
                </div>
                {error && output && <p className="text-xs text-red-500">{error}</p>}
              </div>
            </div>

            {/* Citations — collapsible raw JSON */}
            {citations && (
              <div>
                <Button variant="ghost" size="sm" onClick={() => setShowCitations(!showCitations)}>
                  {showCitations ? 'Hide' : 'Show'} citations ({citations.length})
                </Button>
                {showCitations && (
                  <ScrollArea className="mt-2 max-h-[400px]">
                    <pre className="text-xs bg-muted rounded-md p-4 overflow-x-auto">
                      {JSON.stringify(citations, null, 2)}
                    </pre>
                  </ScrollArea>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
