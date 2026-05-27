# developer-docs/internal/

Internal-only docs. Committed to GitLab; filtered from GitHub release by `infra/scripts/github-push.sh` (path is in `EXCLUDE_PATHS`).

- Use this section for material that should stay inside Amazon — internal release runbooks, ops notes, links to Brazil/Apollo/Pipelines/Taskei, etc.
- Sidebar autogenerates from disk. The section is visible whenever this directory exists; filtering it out at release time hides it from the GitHub docs site without code changes.
- Do **not** link to `internal/` pages from any public-facing page (anything outside `internal/`). Those links would 404 on the published GitHub site.
- Front matter conventions match the rest of `developer-docs/`: `title` required, `sidebar_position` for ordering, `title: Overview` on category index pages.
- To remove the entire section locally, delete the directory — Docusaurus regenerates the sidebar without it.
