---
title: Design System
sidebar_position: 5
---

# web-client Design System

This document specifies the web-client's visual language in a tool-agnostic
form, extracted from the running implementation. Its purpose is narrow and
practical: when a builder or an AI design tool extends the UI, new components
must be indistinguishable from the ones already present. The goal is not "looks
nice" but "looks like it was always part of this application."

The system is a lightly customized [shadcn/ui](https://ui.shadcn.com/)
foundation built on Tailwind CSS v4. Every rule below is either a convention the
codebase already follows or a constraint the codebase already imposes. Following
it makes new work merge cleanly; ignoring it makes new work read as bolted on.

The design system is deliberately closed. Extend it by composing existing
tokens, not by adding new ones. Do not introduce a new color, a new font, a new
radius, or a new spacing unit. An AI design tool consuming this document should
treat [Rules for generated UI](#13-rules-for-generated-ui) as the compressed
checklist; the sections before it supply the reasoning and vocabulary.

---

## 1. The core idea: semantic tokens, never raw values

Every color in this application is referenced through a semantic CSS custom
property, never a raw hex or OKLCH literal and never a Tailwind palette utility
such as `bg-neutral-800`. Token names describe role, not appearance:
`background`, `foreground`, `primary`, `muted`, `border`, `destructive`. This
naming is what allows light mode, dark mode, and five color themes to work from
one set of markup.

```tsx
// WRONG — hard-coded, breaks dark mode and theming
<div className="bg-white text-gray-900 border-gray-200">

// WRONG — Tailwind palette utility, bypasses the token layer
<div className="bg-neutral-50 text-neutral-900 border-neutral-200">

// RIGHT — semantic tokens, adapt to every theme automatically
<div className="bg-background text-foreground border-border">
```

The tokens are defined once in `src/index.css` in the OKLCH color space, mapped
to Tailwind utilities through `@theme inline`, and re-declared under `.dark` and
each `.theme-*` class. Building a feature does not require editing this file. The
correct interaction is to consume the tokens, not add to them.

### The token catalogue

Each row is a foreground/background pair. The `-foreground` token is the
guaranteed-legible text or icon color to place on the base token. Never pair a
foreground with a base other than its own.

| Token (utility) | Role | `-foreground` pair |
|---|---|---|
| `background` / `foreground` | Application canvas and default text | — |
| `card` / `card-foreground` | Raised surface (panels, cards) | Yes |
| `popover` / `popover-foreground` | Floating surface (menus, tooltips) | Yes |
| `primary` / `primary-foreground` | Primary action, active state, brand accent | Yes |
| `secondary` / `secondary-foreground` | Secondary action, low-emphasis fill | Yes |
| `muted` / `muted-foreground` | Subdued surface and subdued text (captions, hints) | Yes |
| `accent` / `accent-foreground` | Hover fill, selected row, subtle highlight | Yes |
| `destructive` | Danger action, error text and border | Uses `white` on-color |
| `border` | Hairline borders and dividers | — |
| `input` | Form-control border (stronger in dark mode) | — |
| `ring` | Focus ring color | — |
| `chart-1` … `chart-5` | Categorical data-visualization series | — |
| `sidebar*` | Sidebar-scoped variants of the above | Yes |

Usage utilities follow Tailwind conventions: `bg-*`, `text-*`, `border-*`,
`ring-*`, `fill-*`. Express opacity with the slash modifier — `bg-primary/90`
for hover, `ring-ring/50` for focus, `text-destructive/90`. This
opacity-on-token pattern is how the application derives hover, active, and
disabled shades instead of defining separate darker or lighter tokens. Match it.

```tsx
// The canonical hover patterns, seen throughout the button and badge variants:
'bg-primary text-primary-foreground hover:bg-primary/90'
'bg-secondary text-secondary-foreground hover:bg-secondary/80'
'hover:bg-accent hover:text-accent-foreground'   // ghost and outline hover
```

---

## 2. Color, formally

- **The color space is OKLCH.** All tokens are authored as `oklch(L C H)`.
  Components consume tokens rather than writing OKLCH by hand. If a one-off
  accent is ever required inside a self-contained artifact, author it in OKLCH
  so it sits in the same perceptual space.
- **The base is neutral (grayscale).** In the default theme, `background`,
  `foreground`, `card`, `muted`, and `border` are pure-gray OKLCH values
  (chroma of 0). Color enters the UI almost exclusively through `primary` and
  the chart series. This restraint is the application's signature: a near-
  monochrome shell with a single accent hue. Do not add a second decorative hue.
- **`primary` is the only themed slot.** The color themes (`default`, `amazon`,
  `blue`, `green`, `amber`, `mono`) each redefine only `--primary` and
  `--primary-foreground`. Everything else stays neutral. This is why a blue
  application and an amber application feel like the same application in two
  coats: the chrome is identical and one accent has moved.
- **Dark mode is re-authored, not inverted.** The `.dark` class provides its own
  OKLCH values (for example, `card` becomes `oklch(0.205 0 0)` and borders
  become `oklch(1 0 0 / 10%)`, white at 10 percent alpha). Because components use
  tokens, adaptation is automatic. Verify contrast when introducing an opacity
  modifier, because `/50` on a dark token behaves differently than on a light
  one.

### Contrast obligations

- Body text on its surface must meet WCAG AA (4.5:1). Large text and UI chrome
  must meet 3:1. The foreground/background token pairs are pre-tuned to pass,
  which is the reason to use the pairs rather than mixing tokens.
- `muted-foreground` is the floor for legible text. Do not go dimmer for content
  intended to be read.
- Never signal state with color alone. Errors carry `destructive` color together
  with a message or icon.

---

## 3. Typography

- **The font stack is system-first.** The application does not ship a webfont.
  `--font-sans` resolves to the platform UI sans through Tailwind's default
  stack; `--font-mono` resolves to the platform monospace. The `mono` theme
  swaps the entire UI to the mono stack (`--font-sans: var(--font-mono)`). Do
  not import Google or Adobe fonts.
- **The type scale is Tailwind's default**, consumed as utilities. The
  vocabulary in use, smallest to largest:

  | Utility | Typical use |
  |---|---|
  | `text-xs` | Badges, table metadata, `xs` buttons, chart labels |
  | `text-sm` | Default body and control text (buttons, inputs, card descriptions) |
  | `text-base` | Long-form paragraph copy |
  | `text-lg` | Card titles in dense layouts |
  | `text-2xl` | Page headings (the page-title `<h2>`) |

  `text-sm` is the workhorse; most interactive text is small. Page titles use
  `text-2xl font-semibold tracking-tight`. Reuse that exact recipe for a new page
  heading.

- **Weight carries hierarchy, not size alone.** The application uses
  `font-medium` (buttons, badges, navigation) and `font-semibold` (titles). It
  rarely uses `font-bold`. Titles use `leading-none`; body copy uses default
  leading.
- **`tracking-tight`** applies to large headings; default tracking applies
  elsewhere.
- **Rendered markdown** uses the `@tailwindcss/typography` `prose` classes (see
  `markdown-content.tsx`). For long-form rendered content, wrap the container in
  `prose dark:prose-invert` rather than hand-styling paragraphs.

---

## 4. Spacing, radius, and sizing

### Spacing scale

The application uses Tailwind's 4px-based scale, consumed as `gap-*`, `p-*`,
`m-*`, and `space-*`. The recurring rhythm:

- **`gap-2`** (8px) — between inline controls (icon and label, header items).
- **`gap-4`** / **`gap-6`** (16 / 24px) — between stacked sections. The
  responsive pattern `gap-4 md:gap-6` is standard.
- **`gap-8`** / **`p-8`** (32px) — page-level padding on content pages.
- **`px-4 lg:px-6`** — the standard horizontal page and header inset. Note the
  responsive step-up.

Prefer `gap-*` on a flex or grid parent over margins on children. The
application is overwhelmingly `flex flex-col gap-*` for vertical stacks.

### Radius

One radius variable drives everything: `--radius: 0.625rem` (10px). Derived
steps are exposed as `rounded-sm`, `rounded-md`, `rounded-lg`, and `rounded-xl`
(each ±4px around the base). Usage:

- `rounded-md` — buttons, inputs, non-pill badges, small controls.
- `rounded-xl` — cards and large surfaces.
- `rounded-full` — pill badges, avatars, round icon-only buttons.
- The `mono` theme forces `rounded-none` on everything, so never rely on a
  corner radius to communicate meaning; it may be squared off.

Use the `rounded-*` utilities, never a raw `border-radius`.

### Component sizing

Controls are sized on a fixed height ladder so they align on a row. The button
variants are the reference for all interactive control heights:

| Size | Height | Use |
|---|---|---|
| `xs` | `h-6` (24px) | Dense toolbars, inline table actions |
| `sm` | `h-8` (32px) | Compact controls, header controls |
| `default` | `h-9` (36px) | Standard buttons and inputs |
| `lg` | `h-10` (40px) | Prominent calls to action |
| `icon` / `icon-sm` / `icon-lg` | `size-9` / `size-8` / `size-10` | Square icon buttons |

Icons inside controls are `size-4` (16px) by default and `size-3` in `xs`. The
variant rule `[&_svg:not([class*='size-'])]:size-4` enforces this. Match it when
hand-placing an icon.

---

## 5. Iconography

- **Two libraries, by domain.** Use `lucide-react` for in-component and control
  icons (buttons, toggles, inline). Use `@tabler/icons-react` (the `Icon*` names)
  for navigation, the sidebar, and larger structural chrome. When in doubt for a
  control, use lucide to match `components/ui/`.
- **The default icon size is `size-4`**, and stroke inherits `currentColor`, so
  an icon takes the text color of its container automatically. Do not set icon
  color explicitly unless deviating on purpose.
- Icon-only buttons must carry an accessible label: a
  `<span className="sr-only">` (see `mode-toggle.tsx`) or an `aria-label`.

---

## 6. Component architecture

Understanding the construction pattern is what allows generated components to
slot in.

### 6.1 The `cn()` merge utility

Every component composes classes through `cn()` (`src/lib/utils.ts`):

```ts
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

`clsx` handles conditionals; `twMerge` de-duplicates conflicting Tailwind
classes so a caller's `className` can override a default. Always pass `className`
through `cn(...)` last so consumers can override. Never concatenate class name
strings.

### 6.2 CVA for variants

Multi-variant components (button, badge, alert) declare their styles with
[class-variance-authority](https://cva.style/). The shape is invariant across
the codebase:

```ts
const thingVariants = cva(
  'BASE classes shared by every variant',   // layout, focus, disabled, svg sizing
  {
    variants: {
      variant: { default: '…', secondary: '…', destructive: '…', outline: '…', ghost: '…', link: '…' },
      size:    { default: '…', sm: '…', lg: '…', icon: '…' },
    },
    defaultVariants: { variant: 'default', size: 'default' },
  },
)
```

The standard variant vocabulary follows. Reuse these names rather than inventing
synonyms:

- `default` — primary filled (`bg-primary`)
- `secondary` — low-emphasis filled (`bg-secondary`)
- `destructive` — danger (`bg-destructive` or `text-destructive`)
- `outline` — bordered, transparent fill, hover to `accent`
- `ghost` — no border or fill, hover to `accent`
- `link` — text only, underline on hover

A new interactive component should expose these variant names where they apply.

### 6.3 The `data-slot` convention

Every primitive stamps a `data-slot="<name>"` attribute, and often
`data-variant` and `data-size`, on its root and sub-parts:

```tsx
<div data-slot="card" className={cn('bg-card …', className)} />
<Comp data-slot="button" data-variant={variant} data-size={size} … />
```

This is the application's styling hook for cross-cutting rules. The `mono` theme,
the `theme-scaled` density adjustments, and chart internals all target
`[data-slot='…']`. When building a compound component, stamp `data-slot` on each
meaningful part so it participates in these global adjustments.

### 6.4 Composition with `asChild` and Radix `Slot`

Interactive primitives accept `asChild` and render through the Radix `Slot`
component so they can project their styling onto a child element (for example, a
button that is actually a router `<Link>`). Preserve this pattern: an anchor
styled as a button is `<Button asChild><Link/></Button>`, not a re-styled `<a>`.

### 6.5 Where components live

- `src/components/ui/` holds shadcn primitives. Never edit these directly. They
  are treated as vendored third-party code and are regenerated with the shadcn
  CLI or MCP. They are excluded from tests and coverage.
- `src/components/` holds shared application components composed from primitives.
- To customize a primitive, wrap it in `src/components/`; do not fork it.

The full component inventory and a live demo are available at the in-application
Kitchen Sink (`/sink`) and in [ShadCN UI / Kitchen Sink](shadcn-kitchen-sink).
Before building a new control, check whether a primitive already exists. It
almost always does — dialog, drawer, sheet, popover, command palette, data
table, carousel, chart, and form are all present.

---

## 7. Interaction and state styling

These states are baked into the base layer of the CVA variants. Reproduce them
on any new interactive element.

- **Focus (keyboard):** `outline-none focus-visible:ring-[3px]
  focus-visible:ring-ring/50 focus-visible:border-ring`. A 3px ring in the
  `ring` token at 50 percent opacity is the application's universal focus signal.
  Do not remove `outline-none` without providing the ring, and never ship a
  control with no visible focus state.
- **Disabled:** `disabled:pointer-events-none disabled:opacity-50`.
- **Invalid (forms):** driven by `aria-invalid` —
  `aria-invalid:border-destructive aria-invalid:ring-destructive/20`. Set the
  ARIA attribute and the styling follows. See `field.tsx` and `form.tsx`.
- **Hover:** the opacity or `accent` patterns from Section 1. Wrap color and
  shadow transitions in `transition-all` or `transition-[color,box-shadow]`,
  because the primitives animate state changes and abrupt hovers read as foreign.
- **Loading:** the `Spinner` primitive is a `size-4 animate-spin` loader with
  `role="status"` and `aria-label="Loading"`. Reuse it rather than hand-rolling
  a spinner. Skeletons use the `Skeleton` primitive.
- **Shadows are minimal.** Outline buttons use `shadow-xs` and cards use
  `shadow-sm`. The application is nearly flat. Do not reach for `shadow-lg` or
  `shadow-xl` on inline UI, and note that the `mono` theme strips shadows
  entirely.

---

## 8. Layout

- **The application shell** (`RootLayout`) is a shadcn sidebar-inset pattern:
  `SidebarProvider` wraps `AppSidebar variant="inset"` and a `SidebarInset` that
  contains a sticky `SiteHeader` and the routed `<Outlet />`. New top-level pages
  render into the outlet and do not recreate chrome.
- **Header height** is the `--header-height` variable. The header is a
  `flex h-(--header-height) items-center` bar with breadcrumbs on the left and
  the theme, mode, and drawer controls pushed right with `ml-auto`.
- **The page body idiom** is `flex flex-1 flex-col gap-* p-*`. Pages are vertical
  flex columns that fill remaining height (`flex-1`). Section rhythm is
  `gap-4 md:gap-6`.
- **Container queries** are in use (`@container/main`, `@container/card-header`),
  so responsive behavior sometimes keys off container size rather than viewport
  size. Prefer Tailwind's `@`-prefixed container variants where a component must
  adapt to its slot rather than the window.
- **Responsive behavior** uses Tailwind default breakpoints. The common step-up
  is `md:` and `lg:` for padding and gap, and `sm:` or `hidden sm:block` to drop
  secondary chrome on small screens. A `use-mobile` hook provides JavaScript-side
  breakpoint logic for sidebar and drawer behavior. Content must reflow to a
  phone width with no horizontal scroll.
- **The density modifier** is the `-scaled` set of themes, which shrink
  `--radius`, text sizes, and the `--spacing` unit at widths of 1024px and above
  for information-dense screens. Because it rescales the base spacing unit,
  `gap-*` and `p-*` values scale with it automatically — a further reason to use
  the scale utilities rather than fixed pixels.

---

## 9. Data visualization

- Charts use [Recharts](https://recharts.org/) wrapped by the shadcn
  `ChartContainer` and `ChartConfig` primitive (`components/ui/chart.tsx`).
  Series colors come from the `--chart-1` through `--chart-5` tokens, which have
  distinct light and dark values, fed through a `ChartConfig` object rather than
  hard-coded colors.
- Charts default to `aspect-video`, `text-xs` labels, and `muted-foreground`
  axis text. Grid and cursor lines use the `border` and `muted` tokens. Reuse the
  container so tooltips, legends, and theming stay consistent.
- Tabular data uses the `Table` primitive together with
  [`@tanstack/react-table`](https://tanstack.com/table) (see the `data-table`
  implementations under `pages/*/components/`). For any sortable or filterable
  table, compose the existing data-table pieces rather than building a new one.

---

## 10. Motion

- **The default motion budget is low.** Transitions are confined to state changes
  such as hover, open and close, and theme mode. The `tw-animate-css` package
  provides the enter and exit animations that the Radix primitives use for
  dialogs, popovers, drawers, and accordions. Those are already wired; using the
  primitive supplies them.
- Route transitions show a top NProgress bar tinted with `--primary`.
- Do not add decorative or looping animation to content UI. Any added motion must
  respect `prefers-reduced-motion`, which the animation utilities already gate
  on.

---

## 11. Theming: one UI, many skins

Two independent axes multiply together.

1. **Light and dark.** The `next-themes` package toggles the `.dark` class on
   `<html>` (`ThemeProvider` and `ModeToggle`). It resolves the system
   preference by default.
2. **Color theme.** The `ActiveThemeProvider` (`active-theme.tsx`) toggles a
   `theme-<name>` class on `<body>`, and `ThemeSelector` sets it. Options are
   `default`, `amazon`, `blue` (the shipped default is `blue-scaled`), `green`,
   `amber`, and `mono`, each with an optional `-scaled` density variant.

Anything built must survive all combinations of these axes — six color themes,
two modes, and scaled or unscaled density. That coverage is automatic if and only
if the component obeys Section 1 and uses semantic tokens only. The most common
way generated UI breaks is a hard-coded color that looks acceptable in
light-default and vanishes in dark-mono.

---

## 12. Accessibility

These are obligations, not suggestions.

- Use semantic HTML first: real `<button>`, `<a>`, `<nav>`, `<header>`, and a
  correct heading hierarchy. Radix primitives supply correct roles and ARIA;
  prefer them over `div` with `onClick`.
- Every icon-only control carries an `sr-only` label or an `aria-label`.
- Every interactive element has a visible keyboard focus state (the
  `focus-visible` ring from Section 7). Never apply `outline: none` without a
  replacement.
- Form fields associate a `<Label htmlFor>` with the control, and invalid state
  uses `aria-invalid` together with a text message.
- Color is never the sole carrier of meaning.
- Contrast follows Section 2. Verify in dark mode, not only light mode.

---

## 13. Rules for generated UI

This is the compressed checklist. When a tool produces or restyles a component
for this application, every item must be true.

1. **Tokens only.** Colors come from semantic tokens (`bg-background`,
   `text-foreground`, `bg-primary`, `text-muted-foreground`, `border-border`,
   `bg-destructive`). Use zero hex, rgb, hsl, or OKLCH literals and zero
   `*-neutral-*`, `*-gray-*`, or `*-blue-*` palette utilities in component
   markup.
2. **Foreground pairs.** On-color text and icons use the matching `-foreground`
   token, never a foreground on a mismatched base.
3. **Derive shades with opacity** (`/90`, `/50`), not new tokens.
4. **Reuse the radius, size, and spacing scales** — `rounded-md`, `rounded-xl`,
   and `rounded-full`; the `h-6/8/9/10` control ladder; the 4px `gap-*` and
   `p-*` scale. Use no arbitrary pixel values where a scale utility exists.
5. **Compose classes through `cn(...)`** with the consumer's `className` merged
   last so it can override.
6. **Multi-variant components use CVA** with the standard variant names
   (`default`, `secondary`, `destructive`, `outline`, `ghost`, `link`) and a
   `size` axis where relevant.
7. **Stamp `data-slot`** on each meaningful part, and support `asChild` for
   interactive primitives that may need to project onto a child.
8. **Reproduce the state styles** verbatim: the `focus-visible:ring-[3px]
   ring-ring/50` focus ring, `disabled:opacity-50 disabled:pointer-events-none`,
   the `aria-invalid` styling, and `transition-*` on state changes.
9. **Icons** use lucide for controls and tabler for navigation, at `size-4`, in
   `currentColor`, and labeled when icon-only.
10. **Check `components/ui/` first.** If a primitive exists, compose it; do not
    reinvent it. Customize by wrapping in `src/components/`, never by editing
    `components/ui/`.
11. **Type** page titles as `text-2xl font-semibold tracking-tight` and body as
    `text-sm`, expressing hierarchy through weight (`font-medium`,
    `font-semibold`), not through bold at a large size.
12. **Verify across themes** — light and dark, and at least the `default` and
    `mono` color themes. The `mono` theme squares corners and drops shadows, and
    the component must still read correctly.
13. **Stay flat.** Use `shadow-sm` on cards and `shadow-xs` on outline controls,
    and nothing heavier on inline UI.
14. **Add no new fonts, no external assets, and no decorative animation.**

### Minimal reference: a token-correct component

```tsx
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const calloutVariants = cva(
  // base: layout and transition shared by all variants
  'rounded-xl border px-4 py-3 text-sm transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground border-border',
        muted: 'bg-muted text-muted-foreground border-transparent',
        destructive: 'bg-card text-destructive border-destructive/30',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export function Callout({
  className,
  variant,
  ...props
}: React.ComponentProps<'div'> & VariantProps<typeof calloutVariants>) {
  return (
    <div
      data-slot="callout"
      data-variant={variant ?? 'default'}
      className={cn(calloutVariants({ variant }), className)}
      {...props}
    />
  )
}
```

This component inherits light and dark mode, all six color themes, the scaled
density mode, and the mono squared-corner treatment without a single line of
theme-specific code, because it speaks only in tokens and scale utilities. That
is the entire design system in one example.

---

## 14. Source of truth

When this document and the code disagree, the code wins. The authoritative files
are:

| Concern | File |
|---|---|
| Design tokens (OKLCH), themes, dark mode, scaled and mono modifiers | `src/index.css` |
| shadcn configuration (style `new-york`, base color `neutral`, aliases) | `components.json` |
| Class-merge utility | `src/lib/utils.ts` |
| Variant pattern reference | `src/components/ui/button.tsx`, `badge.tsx`, `alert.tsx` |
| Component primitive inventory | `src/components/ui/` and [Kitchen Sink](shadcn-kitchen-sink) |
| Theme-switching machinery | `src/components/active-theme.tsx`, `theme-selector.tsx`, `mode-toggle.tsx`, `src/providers/ThemeProvider.tsx` |
| Layout shell | `src/layouts/RootLayout.tsx`, `src/components/site-header.tsx`, `app-sidebar.tsx` |
| Chart theming | `src/components/ui/chart.tsx` |
