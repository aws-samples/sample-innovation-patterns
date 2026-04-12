// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
export interface Preset {
  id: string
  name: string
  systemPrompt: string
  userPromptTemplate?: string
  temperature?: number
  maxTokens?: number
}

export const presets: Preset[] = [
  {
    id: '9cb0e66a-9937-465d-a188-2c4c4ae2401f',
    name: 'Grammatical Standard English',
    systemPrompt:
      'You are a writing assistant. Correct grammar and improve clarity while preserving meaning.',
    userPromptTemplate: 'Paste text to correct...',
    temperature: 0.3,
  },
  {
    id: '61eb0e32-2391-4cd3-adc3-66efe09bc0b7',
    name: 'Summarize for a 2nd grader',
    systemPrompt: 'Summarize the following text in simple language a 2nd grader would understand.',
    temperature: 0.5,
  },
  {
    id: 'a4e1fa51-f4ce-4e45-892c-224030a00bdd',
    name: 'Text to command',
    systemPrompt:
      'Convert the following natural language description into a shell command. Return only the command.',
    temperature: 0.2,
    maxTokens: 256,
  },
  {
    id: 'cc198b13-4933-43aa-977e-dcd95fa30770',
    name: 'Q&A',
    systemPrompt:
      'Answer the following question accurately and concisely. If you are unsure, say so.',
    temperature: 0.5,
  },
  {
    id: 'adfa95be-a575-45fd-a9ef-ea45386c64de',
    name: 'English to other languages',
    systemPrompt:
      'Translate the following English text to the language specified by the user. Return only the translation.',
    temperature: 0.3,
  },
  {
    id: 'c569a06a-0bd6-43a7-adf9-bf68c09e7a79',
    name: 'Parse unstructured data',
    systemPrompt:
      'Extract structured data from the following unstructured text. Return the result as JSON.',
    temperature: 0.2,
    maxTokens: 1024,
  },
  {
    id: '15ccc0d7-f37a-4f0a-8163-a37e162877dc',
    name: 'Classification',
    systemPrompt:
      'Classify the following text into the most appropriate category. Return only the category name.',
    temperature: 0.1,
    maxTokens: 64,
  },
  {
    id: '4641ef41-1c0f-421d-b4b2-70fe431081f3',
    name: 'Natural language to Python',
    systemPrompt:
      'Convert the following natural language description to Python code. Return only the code.',
    temperature: 0.2,
    maxTokens: 1024,
  },
  {
    id: '48d34082-72f3-4a1b-a14d-f15aca4f57a0',
    name: 'Explain code',
    systemPrompt: 'Explain the following code in plain English. Be concise but thorough.',
    temperature: 0.5,
  },
]
