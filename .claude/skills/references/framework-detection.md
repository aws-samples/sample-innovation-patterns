# Framework Detection Reference

Shared detection logic for documentation skills. Referenced by ai-code-docs-dev and ai-code-docs-user.

## Detection Priority

1. **CLAUDE.md Context** (highest signal) — Check for doc paths, framework name, conventions, guidance file pointers
2. **Framework Detection** (filesystem probing) — Match config files to frameworks
3. **Heuristic Discovery** (fallback) — Look for common doc directories

## Framework Detection Table

| Config file | Framework | Typical docs location |
|---|---|---|
| `docusaurus.config.{ts,js}` | Docusaurus | `docs/` or `website/docs/` |
| `mkdocs.yml` | MkDocs | `docs/` |
| `conf.py` + `index.rst` | Sphinx | `source/` or `docs/source/` |
| `.vitepress/config.{ts,js}` | VitePress | parent of `.vitepress/` |
| `book.toml` | mdBook | `src/` |
| `_config.yml` + jekyll theme | Jekyll | `docs/` |

## Heuristic Fallback

If no framework detected:
- Look for `docs/`, `documentation/`, `wiki/` directories
- Find concentrations of `.md` files
- Check for `CONTRIBUTING.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`
- **Ask the user** where docs should go
