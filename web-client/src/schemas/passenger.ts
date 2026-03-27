import { z } from 'zod'

export const passengerSchema = z.object({
  ticket: z.string().min(1, 'Ticket is required'),
  name: z.string().min(1, 'Name is required').max(100, 'Name must be 100 characters or less'),
  pclass: z.number().int().min(1, 'Class must be 1-3').max(3, 'Class must be 1-3'),
  survived: z.number().int().min(0).max(1),
  sex: z.enum(['male', 'female']),
  age: z.number().positive('Age must be positive').nullable().optional(),
  sibsp: z.number().int().min(0, 'Cannot be negative'),
  parch: z.number().int().min(0, 'Cannot be negative'),
  fare: z.number().min(0, 'Fare cannot be negative').nullable().optional(),
  cabin: z.string().nullable().optional(),
  embarked: z.enum(['C', 'Q', 'S']).nullable().optional(),
  boat: z.string().nullable().optional(),
  body: z.number().int().positive().nullable().optional(),
  home_dest: z.string().nullable().optional(),
})

export type PassengerFormData = z.infer<typeof passengerSchema>
