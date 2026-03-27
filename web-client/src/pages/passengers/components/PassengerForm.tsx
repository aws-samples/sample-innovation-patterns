import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { passengerSchema, type PassengerFormData } from '@/schemas/passenger'
import { Field, FieldLabel, FieldError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface PassengerFormProps {
  defaultValues: PassengerFormData
  onSubmit: (data: PassengerFormData) => Promise<void>
  formId?: string
}

export function PassengerForm({ defaultValues, onSubmit, formId }: PassengerFormProps) {
  const { control, handleSubmit } = useForm<PassengerFormData>({
    resolver: zodResolver(passengerSchema),
    defaultValues,
    mode: 'onBlur',
  })

  return (
    <form
      id={formId}
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="grid grid-cols-2 gap-4"
    >
      <Controller
        name="name"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid} className="col-span-2">
            <FieldLabel htmlFor="name">Name</FieldLabel>
            <Input {...field} id="name" aria-invalid={fieldState.invalid} />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="pclass"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="pclass">Class</FieldLabel>
            <Select value={String(field.value)} onValueChange={(v) => field.onChange(Number(v))}>
              <SelectTrigger id="pclass">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1st</SelectItem>
                <SelectItem value="2">2nd</SelectItem>
                <SelectItem value="3">3rd</SelectItem>
              </SelectContent>
            </Select>
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="survived"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="survived">Survived</FieldLabel>
            <Select value={String(field.value)} onValueChange={(v) => field.onChange(Number(v))}>
              <SelectTrigger id="survived">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Yes</SelectItem>
                <SelectItem value="0">No</SelectItem>
              </SelectContent>
            </Select>
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="sex"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="sex">Sex</FieldLabel>
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="sex">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
              </SelectContent>
            </Select>
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="age"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="age">Age</FieldLabel>
            <Input
              id="age"
              type="number"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="sibsp"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="sibsp">SibSp</FieldLabel>
            <Input
              {...field}
              id="sibsp"
              type="number"
              value={field.value ?? 0}
              onChange={(e) => field.onChange(Number(e.target.value))}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="parch"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="parch">Parch</FieldLabel>
            <Input
              {...field}
              id="parch"
              type="number"
              value={field.value ?? 0}
              onChange={(e) => field.onChange(Number(e.target.value))}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="fare"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="fare">Fare</FieldLabel>
            <Input
              id="fare"
              type="number"
              step="0.01"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="cabin"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="cabin">Cabin</FieldLabel>
            <Input
              id="cabin"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value || null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="embarked"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="embarked">Embarked</FieldLabel>
            <Select value={field.value ?? ''} onValueChange={(v) => field.onChange(v || null)}>
              <SelectTrigger id="embarked">
                <SelectValue placeholder="—" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="S">Southampton</SelectItem>
                <SelectItem value="C">Cherbourg</SelectItem>
                <SelectItem value="Q">Queenstown</SelectItem>
              </SelectContent>
            </Select>
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="boat"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="boat">Boat</FieldLabel>
            <Input
              id="boat"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value || null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="body"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel htmlFor="body">Body</FieldLabel>
            <Input
              id="body"
              type="number"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />

      <Controller
        name="home_dest"
        control={control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid} className="col-span-2">
            <FieldLabel htmlFor="home_dest">Home/Destination</FieldLabel>
            <Input
              id="home_dest"
              value={field.value ?? ''}
              onChange={(e) => field.onChange(e.target.value || null)}
              aria-invalid={fieldState.invalid}
            />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )}
      />
    </form>
  )
}
