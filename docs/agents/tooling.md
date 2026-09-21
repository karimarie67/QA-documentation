<!-- atlas-v3:tooling:start -->
# Repository tooling and plugin capabilities

This document is the authoritative registry of repository capability status and
usage constraints. A listed capability is not blanket permission and never
overrides repository policy, approvals, or guardrails.

Read this guide before work that depends on a cloud provider, infrastructure
tool, language server, browser driver, source host, tracker, or current
third-party library documentation.

| Plugin | Status | Why it applies | Use when | Prerequisites | Install or state |
|---|---|---|---|---|---|
| `playwright` | recommended | Playwright configuration and tests were detected. | Driving browser workflows and capturing UI evidence for smoke/regression work. | none | `/plugin install playwright@claude-plugins-official` |
| `github` | recommended | The repository remote is hosted on GitHub. | Repository, pull-request, issue, and review operations on GitHub. | none | `/plugin install github@claude-plugins-official` |
| `context7` | recommended | Versioned third-party dependency (@playwright/test) detected. | Checking current, version-specific Playwright API behavior. | none | `/plugin install context7@claude-plugins-official` |
| `typescript-lsp` | unavailable | JavaScript configuration detected, but the typescript-language-server binary is not installed on this machine. | Navigating and editing JS/TS with language-server diagnostics, once the prerequisite is installed. | typescript-language-server | `/plugin install typescript-lsp@claude-plugins-official` |
| `pyright-lsp` | declined | No Python source was found in this repository; discovery's candidate was a false positive. | N/A | pyright-langserver | `/plugin install pyright-lsp@claude-plugins-official` |

`installed` means setup verified the plugin is enabled and any named binary is
available. `recommended` means the repository signals match but installation
still needs human approval. `declined` and `unavailable` are explicit outcomes,
not permission to pretend the capability exists.

Use Context7 when it is installed and a plan or implementation relies on
version-specific external library or framework behavior. Otherwise consult the
primary official documentation and record the source and version used.

Use language-server plugins during code navigation and editing; they supplement
rather than replace the repository's lint, typecheck, and test commands. Use
browser plugins only when a UI or browser run surface exists. Provider, source-
host, tracker, and browser plugins never override Atlas guardrails, repository
permissions, approval policy, or human-only actions.
<!-- atlas-v3:tooling:end -->
