# QA-documentation

A reusable, site-agnostic Playwright QA automation framework. Each client engagement instantiates it from this template and supplies its own site-specific configuration and specs.

## Language

**Engagement**:
A client project this framework has been instantiated for (e.g. the closed Boost.org engagement). Each engagement gets its own repository created from this template.
_Avoid_: Client, project, deployment

**Framework**:
The site-agnostic core of this repo: helpers, generic spec patterns, and config schema that stay the same across every engagement.
_Avoid_: Core, template code

**Site config**:
The engagement-specific values an engagement fills in to point the framework at its actual site: base URLs, selectors, search terms, download-file patterns. Split across `config-helper.js` (URLs and test data) and `selectors.js` (element selectors), by edit cadence rather than merged into one file.
_Avoid_: Site profile, site settings

**Example**:
A trimmed, clearly-labeled worked instance of the framework against a closed engagement, kept for reference rather than live use (e.g. `examples/boost/`). Not run in CI, not delivering ongoing value to that engagement.
_Avoid_: Reference implementation, sample, demo
