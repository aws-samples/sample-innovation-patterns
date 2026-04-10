import { useRef, useState } from 'react'
import { Square } from 'lucide-react'
import { OidcClient } from '@axa-fr/oidc-client'

import { Button } from '@/components/ui/button'
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card'
import { Label } from '@/components/ui/label'
import { MarkdownContent } from '@/components/markdown-content'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { API_BASE_URL } from '@/services/api/baseApi'

import { CodeViewer } from './components/code-viewer'
import { MaxLengthSelector } from './components/maxlength-selector'
import { ModelSelector } from './components/model-selector'
import { PresetSelector } from './components/preset-selector'
import { TemperatureSelector } from './components/temperature-selector'
import { TopPSelector } from './components/top-p-selector'
import { type Model, models, types } from './data/models'
import { type Preset, presets } from './data/presets'

export function PlaygroundPage() {
  const [selectedModel, setSelectedModel] = useState<Model>(models[0])
  const [selectedPreset, setSelectedPreset] = useState<Preset | null>(null)
  const [temperature, setTemperature] = useState([0.7])
  const [topP, setTopP] = useState([0.9])
  const [maxLength, setMaxLength] = useState([256])
  const [prompt, setPrompt] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [output, setOutput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [tokenUsage, setTokenUsage] = useState<{
    inputTokens?: number
    outputTokens?: number
  } | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  function handlePresetChange(preset: Preset) {
    setSelectedPreset(preset)
    setSystemPrompt(preset.systemPrompt)
    if (preset.temperature !== undefined) setTemperature([preset.temperature])
    if (preset.maxTokens !== undefined) setMaxLength([preset.maxTokens])
    setPrompt(preset.userPromptTemplate ?? '')
  }

  async function handleSubmit() {
    if (!prompt.trim()) return
    setIsStreaming(true)
    setOutput('')
    setTokenUsage(null)
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
      const response = await fetch(`${API_BASE_URL}/api/v1/sse/inference/converse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          model_id: selectedModel.id,
          messages: [{ role: 'user', text: prompt }],
          system_prompt: systemPrompt,
          temperature: temperature[0],
          max_tokens: maxLength[0],
          top_p: topP[0],
        }),
        signal: controller.signal,
      })

      if (!response.ok) {
        setOutput(`Error: ${response.status} — ${await response.text()}`)
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
            metadata?: { usage?: { inputTokens?: number; outputTokens?: number } }
          }
          if (data.text) {
            fullText += data.text
            setOutput(fullText)
          }
          if (data.metadata?.usage) setTokenUsage(data.metadata.usage)
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') setOutput(`Error: ${(err as Error).message}`)
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  function handleCancel() {
    abortControllerRef.current?.abort()
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex items-center justify-between gap-2 px-4 py-4 md:h-16">
        <h2 className="pl-4 text-lg font-semibold">Playground</h2>
        <CodeViewer
          modelId={selectedModel.id}
          temperature={temperature[0]}
          maxTokens={maxLength[0]}
          topP={topP[0]}
        />
        <div className="ml-auto flex gap-2">
          <PresetSelector
            presets={presets}
            value={selectedPreset}
            onPresetChange={handlePresetChange}
          />
        </div>
      </div>
      <Separator />
      <div className="min-h-0 flex-1 overflow-hidden px-4 py-6">
        <div className="grid h-full gap-6 md:grid-cols-[1fr_200px]">
          <div className="hidden flex-col gap-6 overflow-y-auto sm:flex md:order-2">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="system-prompt" className="text-sm font-medium">
                  System Prompt
                </Label>
                {systemPrompt && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-muted-foreground h-auto px-2 py-0.5 text-xs"
                    onClick={() => {
                      setSystemPrompt('')
                      setSelectedPreset(null)
                    }}
                  >
                    Clear
                  </Button>
                )}
              </div>
              <Textarea
                id="system-prompt"
                placeholder="Enter a system prompt or select a preset..."
                className="min-h-[80px] resize-none text-xs"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
              />
            </div>
            <Separator />
            <div className="grid gap-3">
              <HoverCard openDelay={200}>
                <HoverCardTrigger asChild>
                  <span className="text-sm leading-none font-medium peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Model
                  </span>
                </HoverCardTrigger>
                <HoverCardContent className="w-[320px] text-sm" side="left">
                  Choose a foundation model from Amazon Bedrock. Different models vary in
                  capability, speed, and cost.
                </HoverCardContent>
              </HoverCard>
            </div>
            <ModelSelector
              types={types}
              models={models}
              value={selectedModel}
              onValueChange={setSelectedModel}
            />
            <TemperatureSelector value={temperature} onValueChange={setTemperature} />
            <MaxLengthSelector value={maxLength} onValueChange={setMaxLength} />
            <TopPSelector value={topP} onValueChange={setTopP} />
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
                  disabled={!prompt.trim()}
                >
                  Submit
                </Button>
              )}
            </div>
          </div>
          <div className="flex min-h-0 flex-1 flex-col gap-4 md:order-1">
            <div className="grid min-h-0 flex-1 grid-rows-[1fr_1fr] gap-6 lg:grid-cols-[1fr_1fr] lg:grid-rows-[1fr]">
              <Textarea
                placeholder="Enter your prompt..."
                className="min-h-0 resize-none overflow-auto p-4"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
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
                {tokenUsage && (
                  <p className="text-muted-foreground text-xs">
                    {tokenUsage.inputTokens} input · {tokenUsage.outputTokens} output tokens
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
