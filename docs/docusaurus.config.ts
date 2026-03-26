import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import {existsSync} from 'fs';
import {resolve} from 'path';

const showWorking = existsSync(resolve(__dirname, 'docs/working'));

const config: Config = {
  title: 'Innovation Patterns',
  tagline: 'Reusable infrastructure patterns for AWS',
  favicon: 'img/favicon.ico',
  future: {v4: true},
  url: 'https://code.aws.dev',
  baseUrl: process.env.CI ? '/innovation-patterns-0a90b6/' : '/',
  onBrokenLinks: 'warn',
  i18n: {defaultLocale: 'en', locales: ['en']},
  markdown: {format: 'detect', mermaid: true},
  themes: ['@docusaurus/theme-mermaid'],
  customFields: {showWorking},

  presets: [
    ['classic', {
      docs: {
        routeBasePath: '/',
        sidebarPath: './sidebars.ts',
        exclude: [
          'working/**/research*.md',
          'working/**/plan.md',
          'working/**/draft.md',
          'working/**/outline.md',
        ],
      },
      blog: false,
      theme: {customCss: './src/css/custom.css'},
    } satisfies Preset.Options],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Innovation Patterns',
      logo: {alt: 'IPA Logo', src: 'img/logo.png'},
      items: [
        {type: 'docSidebar', sidebarId: 'patternsSidebar', label: 'Patterns', position: 'left'},
        {type: 'docSidebar', sidebarId: 'guidesSidebar', label: 'Guides', position: 'left'},
        {type: 'docSidebar', sidebarId: 'userDocsSidebar', label: 'User Docs', position: 'left'},
        {type: 'docSidebar', sidebarId: 'developerDocsSidebar', label: 'Developer Docs', position: 'left'},
        ...(showWorking ? [{
          type: 'docSidebar' as const,
          sidebarId: 'workingSidebar',
          label: 'Working',
          position: 'left' as const,
        }] : []),
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {title: 'Documentation', items: [
          {label: 'Getting Started', to: '/'},
          {label: 'Patterns', to: '/patterns/'},
          {label: 'Developer Docs', to: '/developer-docs/'},
        ]},
      ],
      copyright: `Copyright \u00A9 ${new Date().getFullYear()} Innovation Patterns.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
