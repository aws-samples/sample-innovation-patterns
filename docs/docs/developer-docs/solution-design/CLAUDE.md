# developer-docs/solution-design/

Permanent home for a *solution's* living design/requirements docs (vision · requirements · exploration · architecture). `index.md` is the section landing; `template/` is a copyable per-solution set. A populated section nests one `solution-design/<solution-name>/` dir per solution alongside `template/`.

- `template/` is intentionally **unprefixed** so it renders as a worked example. Do not rename it to `_template/`: this project overrides the docs `exclude` in `docusaurus.config.ts` (`['**/CLAUDE.md','**/AGENTS.md']`), which *replaces* Docusaurus's default `_`-glob — so `_`-prefixed paths render here, they do not hide. To hide content on disk, use a `.archive/` (dot-prefix) dir per the site taxonomy.
- Customer-specific or pre-decision solution content goes under `developer-docs/internal/<solution>/` (filtered from the GitHub release), **not** here — this section ships publicly.
- These are solution-level design docs; do not confuse with the finer-grained engineering specs in `working/specs/<feature>/`.
- Living-doc conventions are load-bearing: every doc carries a status line + `> Last updated:`; each solution's `index.md` carries the Document·Status·Last-updated·Description table. Promotion from `working/` and onward to canonical reference is **copy, not move**.
- Front matter matches `developer-docs/`: `title` required, `title: Overview` on `index.md` landings, `sidebar_position` for ordering.

See the rendered `index.md` (section overview) and the [Solution Design Docs guide](../../guides/solution-design.md) for the document menu, promotion flow, and public/internal choice.
