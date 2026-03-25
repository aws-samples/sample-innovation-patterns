import { defineConfig } from 'vitepress'
import { existsSync, readdirSync } from 'fs'
import { resolve } from 'path'

const specsExist = existsSync(resolve(__dirname, '../specs'))

export default defineConfig({
  title: 'Innovation Patterns Docs',
  description: 'A cohesive platform for reusable innovation patterns',
  srcExclude: ['**/specs/**'],
  cleanUrls: true,

  themeConfig: {
    nav: [
      { text: 'Getting Started', link: '/getting-started/', activeMatch: '/getting-started/' },
      { text: 'Patterns', link: '/patterns/', activeMatch: '/patterns/' },
      { text: 'User Docs', link: '/user-docs/', activeMatch: '/user-docs/' },
      { text: 'Developer', link: '/developer/', activeMatch: '/developer/' },
      { text: 'Guides', link: '/guides/', activeMatch: '/guides/' },
      ...(specsExist ? [{ text: 'Specs', link: '/specs/', activeMatch: '/specs/' }] : []),
    ],

    sidebar: {
      '/getting-started/': [{
        text: 'Getting Started',
        items: [
          { text: 'Overview', link: '/getting-started/' },
          { text: 'Installation', link: '/getting-started/installation' },
        ],
      }],
      '/patterns/': [{
        text: 'Patterns',
        items: [
          { text: 'Overview', link: '/patterns/' },
        ],
      }],
      '/user-docs/': [{
        text: 'User Docs',
        items: [
          { text: 'Overview', link: '/user-docs/' },
        ],
      }],
      '/developer/': [{
        text: 'Developer Guide',
        items: [
          { text: 'Overview', link: '/developer/' },
          { text: 'Contributing', link: '/developer/contributing' },
        ],
      }],
      '/guides/': [{
        text: 'Guides',
        items: [
          { text: 'Overview', link: '/guides/' },
        ],
      }],
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
