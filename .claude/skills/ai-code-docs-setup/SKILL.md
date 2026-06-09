---
name: ai-code-docs-setup
description: "Set up a documentation site with a static site generator (Docusaurus, MkDocs Material, or VitePress). Use this skill when the user says 'set up docs', 'create a docs site', 'docs setup', 'initialize documentation', 'add documentation site', 'set up developer docs', or wants to scaffold a documentation project. Do NOT use for writing doc content (/ai-code-docs-dev, /ai-code-docs-user), project context (/ai-init), or document generation (/aidoc)."
model: opus
effort: high
---

# Agent Code: Documentation Site Setup

You set up a complete documentation site for a project. You scaffold the static site generator, create directory structure with user docs, developer docs, and optional sections, configure a gitignored `specs/` folder for HITL review, and print integration snippets for the user.

## User Input

```text
$ARGUMENTS
```

Consider any user input above before proceeding.

## What This Skill Does

1. Reads `.context/README.md` for project context
2. Checks for an existing documentation site (won't overwrite)
3. Asks 4 questions: framework, sections, location, site title
4. Generates all framework config, directories, and stub pages
5. Configures a gitignored `specs/` directory for HITL review
6. Prints CLAUDE.md snippet and next-step guidance

It does NOT install dependencies, write real content, set up CI/CD, or modify CLAUDE.md directly.

## Context Loading

1. Read `.context/README.md`
   - If not found: PRINT "No project context found at `.context/README.md`. Run `/ai-init` first to set up your project context." STOP
   - Extract Project section (for site title derivation)
   - Extract `output_path.ai-code` from frontmatter (for specs directory path reference)
   - For stack/framework info, read `CLAUDE.md` if present or discover from `package.json`/`pyproject.toml`

## Step 1: Check for Existing Documentation Site

Probe the filesystem for existing framework config files:

1. Glob for `**/docusaurus.config.{ts,js}` in the project root
2. Glob for `**/mkdocs.yml` in the project root
3. Glob for `**/.vitepress/config.{ts,js}` in the project root

| Config file | Framework |
|---|---|
| `docusaurus.config.{ts,js}` | Docusaurus |
| `mkdocs.yml` | MkDocs |
| `.vitepress/config.{ts,js}` | VitePress |

IF an existing framework config is found:
- Tell the user: "A documentation site already exists (`<framework>` detected at `<path>`)."
- Suggest: "Use `/ai-code-docs-dev` to write developer docs or `/ai-code-docs-user` to write user docs."
- STOP. Do not overwrite.

IF nothing is found, continue to Step 2.

## Step 2: Ask Setup Questions

Use AskUserQuestion to ask 4 questions. These determine the entire scaffold.

### Determine Framework Recommendation

Before asking, read the Stack section of `.context/README.md`:
- If Stack mentions TypeScript, JavaScript, or Node.js → recommend **Docusaurus 3**
- If Stack mentions Python → recommend **MkDocs Material**
- Otherwise → recommend **MkDocs Material** (simplest setup, no Node.js required)

Move the "(Recommended)" label to the appropriate option.

### Question 1: Documentation Framework

- Question: "Which documentation framework should we use?"
- Header: "Framework"
- Options:
  - "Docusaurus 3" — React-based, TypeScript config, auto-generated sidebars, richest HITL specs/ support
  - "MkDocs Material" — Python-based, YAML config, navigation tabs, built-in HITL draft support
  - "VitePress" — Vue/Vite-based, TypeScript config, lightweight and fast
- multiSelect: false

Append "(Recommended)" to whichever option the Stack analysis recommends.

### Question 2: Documentation Sections

- Question: "Which documentation sections do you need?"
- Header: "Sections"
- Options:
  - "User Docs (Recommended)" — getting started, installation, usage guides for end users
  - "Developer Docs (Recommended)" — contributing, architecture, development setup for contributors
  - "Guides" — tutorials, how-tos, and walkthroughs
  - "API Reference" — API documentation, endpoint references, SDK docs
- multiSelect: true

### Question 3: Site Location

- Question: "Where should the documentation site live?"
- Header: "Location"
- Options:
  - "docs/ (Recommended)" — standard convention, most frameworks expect this
  - "website/" — common alternative for monorepos
  - "documentation/" — explicit naming
- multiSelect: false

After the user answers, check if the target directory exists and has content files. IF it does:
- Use AskUserQuestion:
  - "Proceed" — continue (skill will not overwrite existing files)
  - "Choose a different location" — ask for a new location
- multiSelect: false

### Question 4: Site Title

Extract the project name from the first sentence of the Project section in `.context/README.md`.

- Question: "What should the documentation site be called?"
- Header: "Site title"
- Options:
  - "`<Project Name>` Docs" — derived from .context/README.md
  - "`<Project Name>`" — just the project name
  - "`<Project Name>` Documentation" — formal naming
- multiSelect: false

## Step 3: Generate Documentation Site

Based on the framework answer from Question 1, follow the corresponding generation path below.

Use `<site-dir>` to refer to the location answer from Question 3 (e.g., `docs/`).
Use `<site-title>` to refer to the title answer from Question 4.
Use `<tagline>` — derive a one-sentence tagline from the Project section of `.context/README.md`.

---

### IF Docusaurus 3:

#### 3a. Create `<site-dir>/package.json`

```json
{
  "name": "<kebab-case-site-title>",
  "version": "0.0.0",
  "private": true,
  "scripts": {
    "docusaurus": "docusaurus",
    "start": "docusaurus start --port 3030",
    "build": "docusaurus build",
    "swizzle": "docusaurus swizzle",
    "deploy": "docusaurus deploy",
    "clear": "docusaurus clear",
    "serve": "docusaurus serve",
    "write-translations": "docusaurus write-translations",
    "write-heading-ids": "docusaurus write-heading-ids",
    "typecheck": "tsc"
  },
  "dependencies": {
    "@docusaurus/core": "3.9.2",
    "@docusaurus/preset-classic": "3.9.2",
    "@docusaurus/theme-mermaid": "^3.9.2",
    "@mdx-js/react": "^3.0.0",
    "clsx": "^2.0.0",
    "prism-react-renderer": "^2.3.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@docusaurus/module-type-aliases": "3.9.2",
    "@docusaurus/tsconfig": "3.9.2",
    "@docusaurus/types": "3.9.2",
    "typescript": "~5.6.2"
  },
  "engines": {
    "node": ">=20.0"
  }
}
```

Replace `<kebab-case-site-title>` with the site title converted to kebab-case.

#### 3b. Create `<site-dir>/tsconfig.json`

```json
{
  "extends": "@docusaurus/tsconfig",
  "compilerOptions": {
    "baseUrl": "."
  }
}
```

#### 3c. Create `<site-dir>/docusaurus.config.ts`

Build the config dynamically based on the user's section selections. The template:

```ts
import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import fs from 'fs';
import path from 'path';

const specsExist = fs.existsSync(path.join(__dirname, 'docs', 'specs'));

const config: Config = {
  title: '<site-title>',
  tagline: '<tagline>',
  favicon: 'img/favicon.ico',
  future: { v4: true },
  url: 'https://example.com',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  markdown: { format: 'detect', mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    ['classic', {
      docs: {
        routeBasePath: '/',
        sidebarPath: './sidebars.ts',
      },
      blog: false,
      theme: { customCss: './src/css/custom.css' },
    } satisfies Preset.Options],
  ],
  themeConfig: {
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: '<site-title>',
      items: [
        /* ONE docSidebar ITEM PER SELECTED SECTION — see mapping below */
        ...(specsExist ? [{
          type: 'docSidebar' as const,
          sidebarId: 'specsSidebar',
          position: 'left' as const,
          label: 'Specs',
        }] : []),
        { href: 'https://github.com/OWNER/REPO', label: 'GitHub', position: 'right' },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            /* ONE LINK PER SELECTED SECTION */
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'GitHub', href: 'https://github.com/OWNER/REPO' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()}. Built with Docusaurus.`,
    },
    prism: { theme: prismThemes.github, darkTheme: prismThemes.dracula },
  } satisfies Preset.ThemeConfig,
};

export default config;
```

**Section-to-navbar mapping** — for each section the user selected, add a navbar item:

| Section | sidebarId | label | Footer link `to` |
|---|---|---|---|
| User Docs | `gettingStartedSidebar` | `Getting Started` | `/getting-started/installation` |
| Developer Docs | `developerSidebar` | `Developer` | `/developer/` |
| Guides | `guidesSidebar` | `Guides` | `/guides/` |
| API Reference | `apiSidebar` | `API` | `/api/` |

Each navbar item follows this pattern:
```ts
{ type: 'docSidebar', sidebarId: '<sidebarId>', position: 'left', label: '<label>' },
```

Each footer link follows this pattern:
```ts
{ label: '<label>', to: '<to>' },
```

Replace `<site-title>`, `<tagline>`, and `OWNER/REPO` with real values.

#### 3d. Create `<site-dir>/sidebars.ts`

Build dynamically based on selected sections:

```ts
import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';
import fs from 'fs';
import path from 'path';

const sidebars: SidebarsConfig = {
  /* ONE AUTOGENERATED SIDEBAR PER SELECTED SECTION */
};

// Specs sidebar — only when the directory exists (gitignored, absent in CI/CD)
const specsDir = path.join(__dirname, 'docs', 'specs');
if (fs.existsSync(specsDir)) {
  sidebars.specsSidebar = [{type: 'autogenerated', dirName: 'specs'}];
}

export default sidebars;
```

**Section-to-sidebar mapping:**

| Section | Sidebar entry |
|---|---|
| User Docs | `gettingStartedSidebar: [{type: 'autogenerated', dirName: 'getting-started'}],` |
| Developer Docs | `developerSidebar: [{type: 'autogenerated', dirName: 'developer'}],` |
| Guides | `guidesSidebar: [{type: 'autogenerated', dirName: 'guides'}],` |
| API Reference | `apiSidebar: [{type: 'autogenerated', dirName: 'api'}],` |

#### 3e. Create `<site-dir>/src/css/custom.css`

```css
:root {
  --ifm-color-primary: #2e8555;
  --ifm-color-primary-dark: #29784c;
  --ifm-color-primary-darker: #277148;
  --ifm-color-primary-darkest: #205d3b;
  --ifm-color-primary-light: #33925d;
  --ifm-color-primary-lighter: #359962;
  --ifm-color-primary-lightest: #3cad6e;
  --ifm-code-font-size: 95%;
  --docusaurus-highlighted-code-line-bg: rgba(0, 0, 0, 0.1);
}

[data-theme='dark'] {
  --ifm-color-primary: #25c2a0;
  --ifm-color-primary-dark: #21af90;
  --ifm-color-primary-darker: #1fa588;
  --ifm-color-primary-darkest: #1a8870;
  --ifm-color-primary-light: #29d5b0;
  --ifm-color-primary-lighter: #32d8b4;
  --ifm-color-primary-lightest: #4fddbf;
  --docusaurus-highlighted-code-line-bg: rgba(0, 0, 0, 0.3);
}
```

#### 3f. Create `<site-dir>/static/img/` directory

Create the directory (empty). The user adds favicon and logo assets later.

#### 3g. Create directory structure and stub pages

For each selected section, create the directories and files:

**IF User Docs selected** — create `<site-dir>/docs/getting-started/`:

`<site-dir>/docs/getting-started/README.md`:
```md
---
title: "Overview"
sidebar_position: 1
slug: /
---

# <site-title>

Welcome to the documentation.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

`<site-dir>/docs/getting-started/installation.md`:
```md
---
sidebar_label: "Installation"
sidebar_position: 2
---

# Installation

How to install and set up the project.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

**IF User Docs NOT selected** — the homepage must go somewhere. Create `<site-dir>/docs/README.md` with `slug: /` as a minimal homepage.

**IF Developer Docs selected** — create `<site-dir>/docs/developer/`:

`<site-dir>/docs/developer/README.md`:
```md
---
title: "Overview"
sidebar_position: 1
---

# Developer Guide

Resources for contributors and maintainers.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

`<site-dir>/docs/developer/contributing.md`:
```md
---
sidebar_label: "Contributing"
sidebar_position: 2
---

# Contributing

How to contribute to the project.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

**IF Guides selected** — create `<site-dir>/docs/guides/`:

`<site-dir>/docs/guides/README.md`:
```md
---
title: "Overview"
sidebar_position: 1
---

# Guides

Tutorials, how-tos, and walkthroughs.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

**IF API Reference selected** — create `<site-dir>/docs/api/`:

`<site-dir>/docs/api/README.md`:
```md
---
title: "Overview"
sidebar_position: 1
---

# API Reference

API documentation and endpoint references.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

**Always** — create `<site-dir>/docs/specs/` directory (empty).

#### 3h. Update `.gitignore`

Read the project's `.gitignore` (create if it doesn't exist). Append these entries if not already present:

```
# Documentation site
<site-dir>/node_modules/
<site-dir>/build/
<site-dir>/.docusaurus/
<site-dir>/.cache-loader/
<site-dir>/docs/specs/
```

Replace `<site-dir>` with the actual directory name.

---

### IF MkDocs Material:

#### 3a. Create `mkdocs.yml` (in project root)

```yaml
site_name: <site-title>
docs_dir: <site-dir>

exclude_docs: |
  /specs/

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.tabs.sticky
    - navigation.sections
    - navigation.indexes
    - navigation.expand
    - navigation.footer
    - navigation.top
    - search.highlight
    - search.suggest
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: black
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search

markdown_extensions:
  - admonition
  - footnotes
  - toc:
      permalink: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
```

Replace `<site-title>` and `<site-dir>` with real values. No explicit `nav:` block — MkDocs auto-discovers from the filesystem.

#### 3b. Create `requirements.txt` (in project root)

```
mkdocs-material==9.*
```

#### 3c. Create directory structure and stub pages

Create `<site-dir>/index.md` (homepage):
```md
# <site-title>

Welcome to the documentation.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

**IF User Docs selected** — create `<site-dir>/getting-started/`:

`<site-dir>/getting-started/index.md`:
```md
# Getting Started

Get up and running with the project.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

`<site-dir>/getting-started/installation.md`:
```md
# Installation

How to install and set up the project.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

**IF Developer Docs selected** — create `<site-dir>/developer/`:

`<site-dir>/developer/index.md`:
```md
# Developer Guide

Resources for contributors and maintainers.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

`<site-dir>/developer/contributing.md`:
```md
# Contributing

How to contribute to the project.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

**IF Guides selected** — create `<site-dir>/guides/`:

`<site-dir>/guides/index.md`:
```md
# Guides

Tutorials, how-tos, and walkthroughs.

> This page is a stub. Use `/ai-code-docs-user` to write content.
```

**IF API Reference selected** — create `<site-dir>/api/`:

`<site-dir>/api/index.md`:
```md
# API Reference

API documentation and endpoint references.

> This page is a stub. Use `/ai-code-docs-dev` to write content.
```

**Always** — create `<site-dir>/specs/` directory (empty).

#### 3d. Update `.gitignore`

Append if not already present:

```
# Documentation site
site/
<site-dir>/specs/
```

---

### IF VitePress:

#### 3a. Package configuration

Check if `package.json` exists in the project root.

**IF `package.json` exists:** Tell the user to run `npm add -D vitepress` and add these scripts manually:
```json
{
  "scripts": {
    "docs:dev": "vitepress dev <site-dir>",
    "docs:build": "vitepress build <site-dir>",
    "docs:preview": "vitepress serve <site-dir>"
  }
}
```

**IF `package.json` does NOT exist:** Create it:
```json
{
  "scripts": {
    "docs:dev": "vitepress dev <site-dir>",
    "docs:build": "vitepress build <site-dir>",
    "docs:preview": "vitepress serve <site-dir>"
  },
  "devDependencies": {
    "vitepress": "^1.6.0"
  }
}
```

#### 3b. Create `<site-dir>/.vitepress/config.ts`

Build dynamically based on selected sections:

```ts
import { defineConfig } from 'vitepress'
import { existsSync, readdirSync } from 'fs'
import { resolve } from 'path'

const specsExist = existsSync(resolve(__dirname, '../specs'))

export default defineConfig({
  title: '<site-title>',
  description: '<tagline>',
  srcExclude: ['**/specs/**'],
  cleanUrls: true,

  themeConfig: {
    nav: [
      /* ONE NAV ITEM PER SELECTED SECTION — see mapping below */
      ...(specsExist ? [{ text: 'Specs', link: '/specs/', activeMatch: '/specs/' }] : []),
    ],

    sidebar: {
      /* ONE SIDEBAR GROUP PER SELECTED SECTION — see mapping below */
      ...(specsExist ? {
        '/specs/': [{
          text: 'Specs (Local Only)',
          items: readdirSync(resolve(__dirname, '../specs'), { withFileTypes: true })
            .filter(d => d.isDirectory())
            .map(d => ({ text: d.name, link: `/specs/${d.name}/` })),
        }],
      } : {}),
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/OWNER/REPO' },
    ],
  },
})
```

**Section-to-config mapping:**

| Section | Nav item | Sidebar key |
|---|---|---|
| User Docs | `{ text: 'Guide', link: '/getting-started/', activeMatch: '/getting-started/' }` | `'/getting-started/': [{ text: 'Getting Started', items: [{ text: 'Overview', link: '/getting-started/' }, { text: 'Installation', link: '/getting-started/installation' }] }]` |
| Developer Docs | `{ text: 'Developer', link: '/developer/', activeMatch: '/developer/' }` | `'/developer/': [{ text: 'Developer Guide', items: [{ text: 'Overview', link: '/developer/' }, { text: 'Contributing', link: '/developer/contributing' }] }]` |
| Guides | `{ text: 'Guides', link: '/guides/', activeMatch: '/guides/' }` | `'/guides/': [{ text: 'Guides', items: [{ text: 'Overview', link: '/guides/' }] }]` |
| API Reference | `{ text: 'API', link: '/api/', activeMatch: '/api/' }` | `'/api/': [{ text: 'API Reference', items: [{ text: 'Overview', link: '/api/' }] }]` |

Replace `<site-title>`, `<tagline>`, and `OWNER/REPO` with real values.

#### 3c. Create directory structure and stub pages

Create `<site-dir>/index.md` (homepage with VitePress hero layout):
```md
---
layout: home
hero:
  name: "<site-title>"
  tagline: "<tagline>"
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/
---
```

If User Docs is not selected, change the hero action link to whichever section was selected first.

For each selected section, create the same directory and stub page structure as MkDocs (using `index.md` files). MkDocs stub page format works for VitePress too — no special frontmatter needed for content pages.

**Always** — create `<site-dir>/specs/` directory (empty).

#### 3d. Update `.gitignore`

Append if not already present:

```
# Documentation site
<site-dir>/.vitepress/dist/
<site-dir>/.vitepress/cache/
<site-dir>/specs/
node_modules/
```

---

## Step 4: Print Integration Snippets

After generating all files, print the following for the user.

### CLAUDE.md Snippet

Print: "Add this to your project's CLAUDE.md:"

**IF Docusaurus:**

```markdown
## Documentation Site

- **Framework:** Docusaurus 3 (TypeScript)
- **Site root:** `<site-dir>/`
- **Content root:** `<site-dir>/docs/`
- **Frontmatter:** `sidebar_position` for page ordering, `sidebar_label` for display names, `draft: true` for HITL-only content
- **File naming:** kebab-case, one topic per file
- **No `_category_.json`** unless a directory needs a non-default label or collapse behavior
- **Local dev:** `cd <site-dir> && npm start` (port 3030)
- **Build:** `cd <site-dir> && npm run build`
- **Specs:** `<site-dir>/docs/specs/` is gitignored — visible locally for review, never deployed
```

Include a line for each selected section showing its path:
- User Docs: `- **User docs:** \`<site-dir>/docs/getting-started/\``
- Developer Docs: `- **Developer docs:** \`<site-dir>/docs/developer/\``
- Guides: `- **Guides:** \`<site-dir>/docs/guides/\``
- API Reference: `- **API docs:** \`<site-dir>/docs/api/\``

**IF MkDocs Material:**

```markdown
## Documentation Site

- **Framework:** MkDocs Material
- **Config:** `mkdocs.yml`
- **Content root:** `<site-dir>/`
- **Convention:** kebab-case directory names; auto-discovered navigation from filesystem
- **Section index pages:** `index.md` in each directory
- **File naming:** kebab-case, one topic per file
- **Local dev:** `mkdocs serve` (port 8000)
- **Build:** `mkdocs build`
- **Specs:** `<site-dir>/specs/` is gitignored; `exclude_docs` in mkdocs.yml excludes from builds
```

Include section path lines as above (without the `docs/` nesting since MkDocs content is directly in `<site-dir>/`).

**IF VitePress:**

```markdown
## Documentation Site

- **Framework:** VitePress
- **Config:** `<site-dir>/.vitepress/config.ts`
- **Content root:** `<site-dir>/`
- **Convention:** kebab-case directory names; sidebar defined in config.ts
- **Section index pages:** `index.md` in each directory
- **File naming:** kebab-case, one topic per file
- **Local dev:** `npm run docs:dev` (port 5173)
- **Build:** `npm run docs:build`
- **Specs:** `<site-dir>/specs/` is gitignored; `srcExclude` in config.ts excludes from builds
```

Include section path lines as above.

### Installation and Verification

Print framework-specific commands:

**IF Docusaurus:**
```
To get started:
  cd <site-dir> && npm install
  cd <site-dir> && npm start
```

**IF MkDocs Material:**
```
To get started:
  pip install -r requirements.txt
  mkdocs serve
```

**IF VitePress:**

If `package.json` was created:
```
To get started:
  npm install
  npm run docs:dev
```

If `package.json` already existed:
```
To get started:
  npm add -D vitepress
  npm run docs:dev
```

### Next Steps

Print:
```
Your documentation site is ready at `<site-dir>/`.

Next steps:
  /ai-code-docs-user  — write user-facing documentation
  /ai-code-docs-dev   — write developer documentation
  /ai-code-create     — create a feature (appears in specs/ for HITL review)
```
