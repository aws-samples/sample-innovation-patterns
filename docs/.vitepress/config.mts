import { defineConfig } from 'vitepress'
import { existsSync, readdirSync, readFileSync, statSync } from 'fs'
import { basename, join, resolve } from 'path'

const docsDir = resolve(__dirname, '..')
const workingExist = existsSync(resolve(docsDir, 'working'))

// Sections that appear in the top nav
const sections = [
  { text: 'Getting Started', dir: 'getting-started' },
  { text: 'Patterns', dir: 'patterns' },
  { text: 'User Docs', dir: 'user-docs' },
  { text: 'Developer', dir: 'developer' },
  { text: 'Infra', dir: 'infra' },
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

type SidebarItem = { text: string; link?: string; items?: SidebarItem[] }

/**
 * Auto-generate sidebar items for a directory by scanning its *.md files
 * and subdirectories recursively. README.md/index.md become the directory index.
 */
function autoSidebar(dir: string, label: string): SidebarItem[] {
  const absDir = resolve(docsDir, dir)
  if (!existsSync(absDir)) return []

  const entries = readdirSync(absDir, { withFileTypes: true })
  const items: (SidebarItem & { order: number })[] = []

  for (const entry of entries) {
    const fullPath = join(absDir, entry.name)

    if (entry.isFile() && entry.name.endsWith('.md')) {
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
      const subDir = `${dir}/${entry.name}`
      const subLabel = (() => {
        const subIndex = [join(fullPath, 'README.md'), join(fullPath, 'index.md')]
          .find(f => existsSync(f))
        return subIndex
          ? getTitle(subIndex, entry.name)
          : entry.name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      })()

      // Recurse into subdirectory
      const children = autoSidebar(subDir, subLabel)
      if (children.length > 0) {
        items.push({
          text: subLabel,
          link: `/${subDir}/`,
          items: children[0].items,
          order: 1,
        })
      } else {
        items.push({
          text: subLabel,
          link: `/${subDir}/`,
          order: 1,
        })
      }
    }
  }

  items.sort((a, b) => a.order - b.order || a.text.localeCompare(b.text))

  return [{ text: label, items: items.map(({ order, ...rest }) => rest) }]
}

/**
 * Register sidebar entries for a directory and all its subdirectories,
 * so VitePress shows a sidebar at every nesting level.
 */
function registerSidebars(sidebar: Record<string, SidebarItem[]>, dir: string, label: string) {
  const absDir = resolve(docsDir, dir)
  if (!existsSync(absDir)) return

  sidebar[`/${dir}/`] = autoSidebar(dir, label)

  for (const entry of readdirSync(absDir, { withFileTypes: true })) {
    if (entry.isDirectory() && !entry.name.startsWith('.')) {
      const subDir = `${dir}/${entry.name}`
      const fullPath = join(absDir, entry.name)
      const subIndex = [join(fullPath, 'README.md'), join(fullPath, 'index.md')]
        .find(f => existsSync(f))
      const subLabel = subIndex
        ? getTitle(subIndex, entry.name)
        : entry.name.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      registerSidebars(sidebar, subDir, subLabel)
    }
  }
}

// Build sidebar from filesystem
const sidebar: Record<string, SidebarItem[]> = {}
for (const section of sections) {
  registerSidebars(sidebar, section.dir, section.text)
}
if (workingExist) {
  registerSidebars(sidebar, 'working', 'Working (Local Only)')
}

export default defineConfig({
  title: 'Innovation Patterns Docs',
  description: 'A cohesive platform for reusable innovation patterns',
  srcExclude: process.env.CI ? ['**/working/**'] : [],
  cleanUrls: true,
  base: '/innovation-patterns-0a90b6/',
  rewrites: {
    'README.md': 'index.md',
    ':path/README.md': ':path/index.md',
  },
  themeConfig: {
    nav: [
      ...sections.map(s => ({
        text: s.text,
        link: `/${s.dir}/`,
        activeMatch: `/${s.dir}/`,
      })),
      ...(workingExist ? [{ text: 'Working', link: '/working/', activeMatch: '/working/' }] : []),
    ],

    sidebar,

    socialLinks: [
      { icon: 'github', link: 'https://github.com/OWNER/REPO' },
    ],
  },
})
