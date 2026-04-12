// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

interface CodeViewerProps {
  modelId: string
  temperature: number
  maxTokens: number
  topP: number
}

export function CodeViewer({ modelId, temperature, maxTokens, topP }: CodeViewerProps) {
  const snippet = `import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")
response = client.converse_stream(
    modelId="${modelId}",
    messages=[{"role": "user", "content": [{"text": "..."}]}],
    inferenceConfig={
        "temperature": ${temperature},
        "maxTokens": ${maxTokens},
        "topP": ${topP},
    },
)
for event in response["stream"]:
    if "contentBlockDelta" in event:
        print(event["contentBlockDelta"]["delta"]["text"], end="")`

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="secondary">View code</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>View code</DialogTitle>
          <DialogDescription>
            Use this code to integrate your current prompt and settings into your application with
            the Amazon Bedrock Converse API.
          </DialogDescription>
        </DialogHeader>
        <div className="rounded-md bg-black p-6">
          <pre className="overflow-x-auto text-sm text-white">
            <code>{snippet}</code>
          </pre>
        </div>
      </DialogContent>
    </Dialog>
  )
}
