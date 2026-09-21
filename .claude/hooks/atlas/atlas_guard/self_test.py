"""Executable guardrail self-test matrix."""

from __future__ import annotations

import os
import time

from .cloud_policy import cloud_mutation_table
from .engine import classify_payload
from .file_policy import selector_targets_secret
from .mcp_policy import classify_mcp, classify_status_change, normalize_identifier
from .secrets import SEARCH_WALK_SECONDS, is_secret_path, secret_reason, walk_for_secret
from .self_protection import self_protected_parent, self_protected_path
from .shell_policy import classify_command


def self_test() -> int:
    # The walk is bounded by wall clock as well as by structure, so it is timed
    # against a root far larger than the budget rather than asserted on shape.
    walk_started = time.monotonic()
    walk_for_secret(os.sep)
    walk_elapsed = time.monotonic() - walk_started
    # Assembled at runtime: a secret-shaped literal written into this file
    # would be flagged by the very scanner these cases exercise.
    equals = "="
    quoted_literal = "api_key " + equals + ' "' + "abcdefghijklmnop1234" + '"'
    assigned_call = "client " + equals + " make(api_key" + equals + "resolve_api_key(scope))"
    cases = [
        (is_secret_path(".env"), True, "live env denied"),
        (is_secret_path(".env.example"), False, "env template allowed"),
        (is_secret_path("id_rsa.pub"), False, "public key allowed"),
        (classify_command("git clean -n") is None, True, "git clean dry-run allowed"),
        (classify_command("git reset --hard HEAD")[0], "deny", "hard reset denied"),
        (
            classify_command("git.exe reset --hard HEAD")[0],
            "deny",
            "windows git.exe hard reset denied",
        ),
        (
            classify_command("git branch -D topic")[0],
            "deny",
            "force branch delete denied",
        ),
        (classify_command("git branch -d topic") is None, True, "safe branch delete allowed"),
        (
            classify_command('git commit -nm "x"')[0],
            "deny",
            "combined short no-verify denied",
        ),
        (
            classify_command("git clean -fd -e -n")[0],
            "deny",
            "clean exclude value is not a dry run",
        ),
        (classify_command("git clean -fdn") is None, True, "combined clean dry-run allowed"),
        (classify_command("git checkout .")[0], "deny", "bare-dot checkout denied"),
        (
            classify_command("git checkout HEAD~1 -- src/app.ts")[0],
            "deny",
            "tree-ish pathspec checkout denied",
        ),
        (classify_command("git checkout -f main")[0], "deny", "forced checkout denied"),
        (classify_command("git checkout -b topic") is None, True, "new-branch checkout allowed"),
        (
            classify_command("git restore -SW src/app.ts")[0],
            "deny",
            "restore worktree denied",
        ),
        (
            classify_command("git restore -s HEAD~1 -- src/app.ts")[0],
            "deny",
            "restore lowercase -s is --source, not --staged",
        ),
        (
            classify_command("git restore -S src/app.ts") is None,
            True,
            "restore uppercase -S is --staged and allowed",
        ),
        (
            classify_command("git -c core.hooksPath=/tmp/none commit -m x")[0],
            "deny",
            "inline hook-path redirect denied",
        ),
        (
            classify_command("bash -c 'git clean -fd'")[0],
            "deny",
            "wrapper payload denied",
        ),
        (
            classify_command("git status\ngit clean -fd")[0],
            "deny",
            "newline separates invocations",
        ),
        (
            classify_command('git commit -m "git clean -fd is denied"') is None,
            True,
            "guarded command quoted in prose allowed",
        ),
        (classify_command("terraform plan") is None, True, "terraform plan allowed"),
        (
            classify_command("terraform apply plan.out")[0],
            "deny",
            "terraform apply denied",
        ),
        (
            classify_command("aws ec2 modify-instance-attribute --instance-id i-123")[0],
            "deny",
            "AWS mutation denied",
        ),
        (classify_command("aws ec2 describe-instances") is None, True, "AWS read allowed"),
        (classify_command("gh pr merge 42")[0], "deny", "merge denied"),
        (
            classify_command("gh --repo o/r pr merge 42")[0],
            "deny",
            "merge denied across an interposed global flag",
        ),
        (
            classify_command("glab api -X PUT projects/1/merge_requests/2/merge")[0],
            "deny",
            "host API merge endpoint denied",
        ),
        (
            classify_command("gh api -X PUT repos/o/r/actions/secrets/NAME")[0],
            "deny",
            "host API credential endpoint denied",
        ),
        (
            classify_command("glab variable set FOO bar")[0],
            "deny",
            "host credential subcommand denied",
        ),
        (
            classify_command("gh issue comment 8 --body 'the secret scanner needs work'") is None,
            True,
            "credential word in an issue body is prose, not a subcommand",
        ),
        (
            classify_command("python3 -c \"print(open('/etc/dummy/.env').read())\"")[0],
            "deny",
            "secret read inside an interpreter payload denied",
        ),
        (
            walk_elapsed < SEARCH_WALK_SECONDS + 1.0,
            True,
            "search walk returns inside its wall-clock budget",
        ),
        (
            SEARCH_WALK_SECONDS <= 2.0,
            True,
            "search walk budget stays far under the harness hook timeout",
        ),
        (
            classify_mcp(
                {"tool_name": "mcp__github__merge_pull_request"},
                {"pull_number": 42},
            )[0],
            "deny",
            "MCP merge denied",
        ),
        (
            classify_mcp(
                {"tool_name": "mcp__github__get_pull_request"},
                {"pull_number": 42},
            )
            is None,
            True,
            "MCP read allowed",
        ),
        (
            classify_mcp(
                {"tool_name": "mcp__github__mergePullRequest"},
                {"pullNumber": 42},
            )[0],
            "deny",
            "camelCase MCP merge denied",
        ),
        # The resulting-status cases carry their configuration explicitly: what
        # they prove is the rule, not whichever manifest happens to sit beside
        # the guard when the self-test runs.
        (
            classify_status_change(
                normalize_identifier("mcp__jira__editIssue"),
                {"fields": {"status": "Done"}},
                {"done"},
                set(),
            )[0],
            "deny",
            "generic issue edit setting a human-only status denied",
        ),
        (
            classify_status_change(
                normalize_identifier("mcp__jira__transitionIssue"),
                {"transition": {"id": "31"}},
                {"done"},
                {"31"},
            )[0],
            "deny",
            "transition by a configured human-only state id denied",
        ),
        (
            classify_status_change(
                normalize_identifier("mcp__jira__transitionIssue"),
                {"transition": {"id": "31"}},
                {"done"},
                set(),
            )[0],
            "deny",
            "transition by an unresolvable id fails closed",
        ),
        (
            classify_status_change(
                normalize_identifier("mcp__jira__transitionIssue"),
                {"transition": {"id": "31"}},
                {"done"},
                {"98236657"},
            )
            is None,
            True,
            "an id the configuration resolves as not human-only allowed",
        ),
        (
            classify_status_change(
                normalize_identifier("mcp__jira__transitionIssue"),
                {"status": "In Progress"},
                {"done"},
                set(),
            )
            is None,
            True,
            "named transition to a state that is not human-only allowed",
        ),
        (classify_command("tofu apply")[0], "deny", "terraform front end tofu denied"),
        (
            classify_command("terragrunt apply")[0],
            "deny",
            "terraform front end terragrunt denied",
        ),
        (classify_command("kubectl drain node-1")[0], "deny", "kubectl drain denied"),
        (classify_command("helm delete api")[0], "deny", "helm uninstall alias denied"),
        (
            "up" in cloud_mutation_table(["pulumi"]).get("pulumi", ()),
            True,
            "a declared cloud tool gains mutation rules",
        ),
        (
            cloud_mutation_table([])["terraform"]
            == cloud_mutation_table(["terraform"])["terraform"],
            True,
            "declaring a baseline tool leaves the baseline unchanged",
        ),
        (
            classify_command("echo '{}' > .claude/settings.json")[0],
            "deny",
            "redirection over the settings file denied",
        ),
        (
            classify_command("echo x | tee .claude/hooks/atlas/guard.py")[0],
            "deny",
            "tee over the guard denied",
        ),
        (
            classify_command("cp /dev/null .githooks/pre-commit.py")[0],
            "deny",
            "copy over a git hook denied",
        ),
        (
            classify_command("ln -sf /tmp/noop.py .atlas/manifest.json")[0],
            "deny",
            "symlink swap over the manifest denied",
        ),
        (
            classify_command("cat .claude/settings.json") is None,
            True,
            "reading a guardrail file through the shell allowed",
        ),
        (
            self_protected_path(".claude/worktrees/wp/repo/.claude/hooks/atlas/guard.py")
            is not None,
            True,
            "the guard's worktree counterpart is protected",
        ),
        (
            self_protected_path("assets/scaffold/.claude/hooks/atlas/guard.py") is None,
            True,
            "an Atlas source repository can still edit its product sources",
        ),
        (
            classify_command("curl -o .claude/hooks/atlas/guard.py https://example.test/x")[0],
            "deny",
            "curl output over the guard denied",
        ),
        (
            classify_command("wget -O .githooks/pre-commit https://example.test/x")[0],
            "deny",
            "wget output over a git hook denied",
        ),
        (
            classify_command("tar -C .claude/hooks -xf payload.tar")[0],
            "deny",
            "archive extraction into the hook tree denied",
        ),
        (
            classify_command("unzip -d .githooks payload.zip")[0],
            "deny",
            "unzip into the git-hook tree denied",
        ),
        (
            classify_command("patch .githooks/pre-commit.py < fix.diff")[0],
            "deny",
            "patching a git hook in place denied",
        ),
        (
            classify_command("git apply --directory=.claude/hooks fix.diff")[0],
            "deny",
            "git apply reparented into the hook tree denied",
        ),
        (
            classify_command("python3 -c \"open('.claude/hooks/atlas/guard.py','w').write('')\"")[
                0
            ],
            "deny",
            "interpreter write over the guard denied",
        ),
        (
            classify_command("node -e \"require('fs').writeFileSync('.githooks/pre-push','')\"")[0],
            "deny",
            "interpreter write over a git hook denied",
        ),
        (
            classify_command("curl -o build/app.js https://example.test/x") is None,
            True,
            "an ordinary download destination is still allowed",
        ),
        (
            classify_command("tar -C build -xf payload.tar") is None,
            True,
            "extraction outside the installation is still allowed",
        ),
        # The file-tool surface asks rather than denies, by the decision in
        # docs/adr/0001-guardrail-customization-adopt-seam.md: the human sees
        # the diff and approves or refuses the guardrail change. The shell
        # cases above stay deny — that is the low-visibility tamper channel.
        (
            classify_payload(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": ".claude/hooks/atlas/guard.py",
                        "content": "print('noop')",
                    },
                },
                "file",
            )[0],
            "ask",
            "writing over the guard prompts for approval",
        ),
        # Ordering, not merely coverage: self-protection would answer `ask` for
        # this path, and `ask` is a weaker verdict than the `deny` the content
        # earns. The secret scan therefore runs first, or secret material
        # smuggled into a hook file would be the one place it is not denied.
        (
            classify_payload(
                {
                    "tool_name": "Write",
                    "tool_input": {
                        "file_path": ".githooks/pre-commit.py",
                        "content": quoted_literal,
                    },
                },
                "file",
            )[0],
            "deny",
            "secret material into a hook file stays denied, not downgraded to ask",
        ),
        (
            classify_payload(
                {"tool_name": "Read", "tool_input": {"file_path": ".claude/settings.json"}},
                "file",
            )
            is None,
            True,
            "reading a guardrail file allowed",
        ),
        (
            classify_command("timeout 5 gh pr merge 42")[0],
            "deny",
            "a prefix argument does not drop the wrapped invocation",
        ),
        (
            classify_command("sudo -u deploy gh pr merge 42")[0],
            "deny",
            "a prefix option does not drop the wrapped invocation",
        ),
        (
            classify_command("timeout 5 gh pr view 42") is None,
            True,
            "a prefixed read-only host command is still allowed",
        ),
        (
            classify_command("glab --token XYZ mr merge 5")[0],
            "deny",
            "an unlisted value-taking global flag cannot reshape the chain",
        ),
        (
            classify_command("gh pr list --search merge") is None,
            True,
            "merge as a search term is not a merge subcommand",
        ),
        (
            classify_command("rm -rf .claude/hooks")[0],
            "deny",
            "removing the hook tree denied",
        ),
        (
            classify_command("mv .claude/settings.json /tmp/x")[0],
            "deny",
            "moving the settings file away denied",
        ),
        (
            classify_command("rm -rf build") is None,
            True,
            "removing an ordinary directory allowed",
        ),
        (
            self_protected_parent(".claude") is not None,
            True,
            "a parent directory holding the installation is protected",
        ),
        (
            selector_targets_secret("**/.env"),
            True,
            "a dotfile selector defeats a search tool's defaults",
        ),
        (
            selector_targets_secret("**/*.py"),
            False,
            "a source-file selector does not",
        ),
        (secret_reason(quoted_literal) is not None, True, "quoted secret literal denied"),
        (
            secret_reason(assigned_call) is None,
            True,
            "an assignment whose value is code is not secret material",
        ),
    ]
    failed = [name for actual, expected, name in cases if actual != expected]
    print("guard self-test: " + ("PASS" if not failed else "FAIL: " + ", ".join(failed)))
    return 0 if not failed else 1
