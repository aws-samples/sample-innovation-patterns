import { defineConfig } from 'vitepress'
import { existsSync, readdirSync, readFileSync, statSync } from 'fs'
import { basename, join, resolve } from 'path'

const docsDir = resolve(__dirname, '..')
const specsExist = existsSync(resolve(docsDir, 'specs'))

// Sections that appear in the top nav
const sections = [
  { text: 'Getting Started', dir: 'getting-started' },
  { text: 'Patterns', dir: 'patterns' },
  { text: 'User Docs', dir: 'user-docs' },
  { text: 'Developer', dir: 'developer' },
  { text: 'Guides', dir: 'guides' },
]

/**
 * Extract the first H1 title from a markdown file, or fall back to
 * converting the filename to title case.
 */
function getTitle(filePath: string, fileName: string): string {
  try {
    const content = readFileSync(filePath, 'utf-8')
    const match = content.match(/^#\s+(.+)$/m)
    if (match) return match[1]
  } catch { /* fall through */ }
  return fileName
    .replace(/\.md$/, '')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

/**
 * Auto-generate sidebar items for a directory by scanning its *.md files
 * and subdirectories. README.md becomes the index (Overview) link.
 */
function autoSidebar(dir: string, label: string): { text: string; items: { text: string; link: string }[] }[] {
  const absDir = resolve(docsDir, dir)
  if (!existsSync(absDir)) return []

  const entries = readdirSync(absDir, { withFileTypes: true })
  const items: { text: string; link: string; order: number }[] = []

  for (const entry of entries) {
    const fullPath = join(absDir, entry.name)

    if (entry.isFile() && entry.name.endsWith('.md')) {
      // README.md and index.md both serve as the section index
      if (entry.name === 'README.md' || entry.name === 'index.md') {
        items.push({ text: 'Overview', link: `/${dir}/`, order: -1 })
      } else {
        const slug = entry.name.replace(/\.md$/, '')
        items.push({
          text: getTitle(fullPath, entry.name),
          link: `/${dir}/${slug}`,
          order: 0,
        })
      }
    }

    if (entry.isDirectory() && !entry.name.startsWith('.')) {
      // Check for an index file inside the subdirectory
      const subIndex = [join(fullPath, 'README.md'), join(fullPath, 'index.md')]
        .find(f => existsSync(f))
      const subLabel = subIndex
        ? getTitle(subIndex, entry.name)
        : entry.name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      items.push({
        text: subLabel,
        link: `/${dir}/${entry.name}/`,
        order: 1,
      })
    }
  }

  // Sort: overview first, then files, then directories
  items.sort((a, b) => a.order - b.order || a.text.localeCompare(b.text))

  return [{ text: label, items: items.map(({ text, link }) => ({ text, link })) }]
}

/**
 * Build rewrites map so README.md files serve as index pages.
 * e.g. getting-started/README.md → getting-started/index.md
 */
function buildRewrites(): Record<string, string> {
  const rewrites: Record<string, string> = {}

  // Top-level README
  if (existsSync(resolve(docsDir, 'README.md'))) {
    rewrites['README.md'] = 'index.md'
  }

  function scan(dir: string) {
    const absDir = resolve(docsDir, dir)
    if (!existsSync(absDir)) return
    for (const entry of readdirSync(absDir, { withFileTypes: true })) {
      if (entry.isFile() && entry.name === 'README.md') {
        rewrites[`${dir}/README.md`] = `${dir}/index.md`
      }
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        scan(`${dir}/${entry.name}`)
      }
    }
  }

  for (const section of sections) scan(section.dir)
  return rewrites
}

// Build sidebar from filesystem
const sidebar: Record<string, ReturnType<typeof autoSidebar>> = {}
for (const section of sections) {
  sidebar[`/${section.dir}/`] = autoSidebar(section.dir, section.text)
}
if (specsExist) {
  sidebar['/specs/'] = autoSidebar('specs', 'Specs (Local Only)')
}

export default defineConfig({
  title: 'Innovation Patterns Docs',
  description: 'A cohesive platform for reusable innovation patterns',
  srcExclude: ['**/specs/**'],
  cleanUrls: true,
  base: '/innovation-patterns-0a90b6/',
  rewrites: buildRewrites(),

  themeConfig: {
    nav: [
      ...sections.map(s => ({
        text: s.text,
        link: `/${s.dir}/`,
        activeMatch: `/${s.dir}/`,
      })),
      ...(specsExist ? [{ text: 'Specs', link: '/specs/', activeMatch: '/specs/' }] : []),
    ],

    sidebar,

    socialLinks: [
      { icon: 'github', link: 'https://github.com/OWNER/REPO' },
    ],
  },
})
