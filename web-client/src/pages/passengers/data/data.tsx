// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import { IconCheck, IconX, IconShip, IconGenderMale, IconGenderFemale } from '@tabler/icons-react'

export const survivedOptions = [
  { value: '1', label: 'Survived', icon: IconCheck },
  { value: '0', label: 'Perished', icon: IconX },
]

export const classOptions = [
  { value: '1', label: '1st Class', icon: IconShip },
  { value: '2', label: '2nd Class', icon: IconShip },
  { value: '3', label: '3rd Class', icon: IconShip },
]

export const sexOptions = [
  { value: 'male', label: 'Male', icon: IconGenderMale },
  { value: 'female', label: 'Female', icon: IconGenderFemale },
]

export const embarkedOptions = [
  { value: 'S', label: 'Southampton' },
  { value: 'C', label: 'Cherbourg' },
  { value: 'Q', label: 'Queenstown' },
]

export const analysisOptions = [
  { value: 'analyzed', label: 'Analyzed' },
  { value: 'pending', label: 'Not Analyzed' },
]
