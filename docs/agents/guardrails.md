<!-- atlas-v3:guardrails:start -->
# Atlas guardrails and hooks

`CLAUDE.md` declares the repository's cross-cutting guardrails and routes agents
here for their authoritative enforcement, activation, exception, and
troubleshooting rules.

## Layers and failure behavior

- Claude `PreToolUse` enforcement blocks live secret access, secret material,
  destructive or bypassing git, remote/credential tampering, protected-branch
  pushes, unsafe egress, and human-only merge actions. It fails closed.
- That enforcement covers commands issued in this session. It does not evaluate
  what runs on a remote host or inside a container: `ssh <host> <command>` and
  `docker exec <container> <command>` are judged as the local `ssh` or `docker`
  call, and the command they carry is never parsed. So
  `ssh prod-host git push --force origin main` is allowed here and runs on the
  remote host. What governs that host is the credential that reaches it, not
  this hook.
- Cloud and infrastructure mutation is denied by default; plan, validate, show,
  diff, and confirmed read-only commands remain available. An exception must be
  durable, narrowly scoped, attributable, environment-specific, and time-bounded.
- Claude's native session and subagent transcripts remain the source for
  retrospective tool-call and token analysis; Atlas does not duplicate commands
  or credentials into repository-local audit logs.
- Git pre-commit checks secret-bearing paths and uses gitleaks when available,
  with a documented lower-strength added-line fallback.
- Git pre-push evaluates resolved refspecs and blocks protected branches and
  remote deletion. Commit-msg enforces the configured conventional subject.
- Atlas verification remains failed until every configured repository has the
  committed git-hook path active.

Secret templates such as `.env.example`, `.env.sample`, `.env.template`, and
public keys remain accessible. Live secret files do not.

Claude permission precedence is `deny` over `ask` over `allow`, regardless of
specificity. A permission mode that suppresses prompts may bypass interactive
`ask`; it cannot override `deny` or an enforcement hook.

## Activation and verification

A human activates committed git hooks. Where no other hook path was configured:

```bash
git config core.hooksPath .githooks
```

Run these commands from the Atlas workspace root, then run `/setup-atlas`
verification afterward. Each generated hook also supports `--self-test`. Never
activate hooks silently during setup.

Where a hook path or a hook manager (husky, pre-commit, lefthook) was already
configured, that command is not the answer: pointing `core.hooksPath` at
`.githooks` detaches every check the existing manager ran, and nothing reports
it — its files stay on disk and its checks simply stop. Setup records the
human's decision instead, as `guardrails.hook_activation`: `standard` (Atlas's
path becomes the configured one), `chain` (the existing manager keeps the
configured path and calls `.githooks/<hook>` from its scripts, including when a
human wires that themselves), or `skip` (Atlas's git hooks stay inactive).
Verification fails rather than reporting green when the configured path shows
Atlas displaced the pre-existing one recorded at setup without a decision that
covers it.

## Transcripts and privacy

Claude's native session and subagent transcripts already contain tool calls,
results, and token usage. Atlas does not copy that sensitive data into local
repository audit logs. Apply the organization's access and retention policy to
Claude transcripts. A compliance-grade audit trail requires an external,
access-controlled or append-only sink rather than agent-writable repository files.

## Secret-scanner suppression

No inline suppression marker exists for the secret-content scanner, by
design. Parsing plus the quoted-literal requirement in the secret-content
patterns removes every reported false-positive class: an assignment whose
*value* is code (a keyword argument or local named for a credential, assigned
the result of a resolver or hashing call) no longer matches, and prose that
merely names or quotes a guarded command or secret-shaped key no longer
matches either. For the residual case — a document that must contain a
realistic quoted secret-shaped literal — the workaround is assembling the
literal at runtime or splitting it across tokens, the same technique this
repository's own tests use, rather than a suppression marker.

## Customizing and maintaining the installed guardrail files

Once installed, `.claude/hooks/**`, `.claude/settings.json`, `.githooks/**`,
and `.atlas/manifest.json` are self-protected on two surfaces, and the two
carry different verdicts deliberately:

- Claude Write/Edit/NotebookEdit on those paths **ask**: the human sees the
  exact diff and approves or refuses the change. This is how a team tailors
  the guardrails to its own risk posture. The accepted cost is that a
  permission mode which suppresses prompts also suppresses this one.
- Shell-level writes stay **denied** by the enforcement hook, which no
  permission mode overrides: redirection, `tee`, `dd`, `cp`, `mv`, in-place
  editors, removal, interpreter `-c`/`-e` program text, `curl -o`/`wget -O`,
  `patch`, `git apply`, and archive extraction. They show no diff and require
  no approval, and the file tools above cover every legitimate edit.

An approved edit initially diverges the installed copy from its recorded
hash, so `verify` reports it and names the remediation: record it. There is no
`scripts/atlas_scaffold.py` to run directly in this repository — it lives
inside the Atlas plugin's own installation, not this checkout, so a bare
relative path does not resolve in a plain shell. Ask Claude Code to run the
`setup-atlas` skill's adopt step (not a full setup or refresh): give it the
file path, the approval reference (a ticket or comment URL), and the
approver's name. The skill resolves the scaffolder's `adopt` command from the
plugin's own installation and hashes the current content itself.

Adoption ties the customization to the approval event that authorized it and
makes it durable. `verify` then reports the file as `customized` — a
sanctioned state, distinct from tampering, with its self-tests still running —
setup reruns preserve the edit instead of conflicting on it, and when a plugin
upgrade moves the canonical asset past the adopted one, the next `apply`
raises a conflict for deliberate re-resolution rather than silently keeping
either side. Editing the file again after adoption is tampering until it is
re-adopted; the recorded hash is what makes those two distinguishable.

The approval reference is attribution by assertion: the scaffolder records the
URL and approver it is given and does not verify them against the event. It is
a durable, reviewable record, not proof.

For plugin maintainers the durable path is still the `assets/scaffold/` source
(or, for settings and the manifest, the setup config), reinstalled through the
scaffolder:

```bash
<python> scripts/atlas_scaffold.py plan --repo . --config <config.json>
<python> scripts/atlas_scaffold.py apply --repo . --config <config.json>
<python> scripts/atlas_scaffold.py verify --repo .
```

The scaffolder's own file writes are not Claude tool calls, so the guard
never intercepts them.

## Exceptions

A human-approved exception records authorizer, exact action, environment,
scope, and expiry in the ticket or spec. Conversation-only approval is invalid.
Do not weaken a hook or permission rule to grant yourself authority.
<!-- atlas-v3:guardrails:end -->
