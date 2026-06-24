# VSCode Configuration

- The following configuration will configure VSCode to:
    - Automatically make available a `app-lib/.venv/` Python virtual environment
    - Allow `ruff` to automatically reformat Python code in the workspace "on save"

- Rename `settings.json.example` to `settings.json` to enable this behavior

``` json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/app-lib/.venv/bin/python",
  "git.openRepositoryInParentFolders": "always",
  "python.analysis.extraPaths": [],
  "notebook.formatOnSave.enabled": true,
  "notebook.codeActionsOnSave": {
    "notebook.source.fixAll": "explicit",
    "notebook.source.organizeImports": "explicit"
  },
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    },
  },
  "makefile.configureOnOpen": false
}
```