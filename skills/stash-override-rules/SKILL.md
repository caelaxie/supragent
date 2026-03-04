---
name: stash-override-rules
description: Create, adjust, and validate Stash VPN override rules (`.stoverride`) for DNS, fake-IP filtering, rules, and routing behavior. Use when asked to build or troubleshoot Stash overrides, install overrides from URL, merge override patches into an active profile, or verify that override changes are actually taking effect at runtime.
---

# Stash Override Rules

## Goal

Produce minimal, safe `.stoverride` patches that solve the user's networking goal without replacing unrelated profile settings.

## Workflow

1. Identify the exact intent and success signal.
- Infer the expected behavior from context when clear.
- Ask a clarifying question only when success criteria are ambiguous.
- Define an observable check (for example DNS resolution, `curl`, or app behavior).

2. Build only the required patch keys.
- Add only keys relevant to the request (for example `dns.fake-ip-filter`).
- Avoid copying a whole base profile into override content.
- Keep the patch short and explicit.

3. Ensure override metadata is present.
- Always include `name` and `desc` in generated override YAML.
- Use a descriptive, task-specific name.

4. Install and enable correctly.
- Install override via Stash Overrides UI or URL scheme.
- Keep base config selected in Configs.
- Enable the override entry in Overrides.

5. Verify runtime effect from terminal.
- Validate the behavior with concrete probes.
- Prefer checks that directly match the request.

## Cross-Agent Compatibility

Use this contract so the skill works across different coding agents and toolchains:

1. Use agent-neutral artifacts.
- Emit plain YAML and shell commands only.
- Avoid agent-specific APIs, memory features, or proprietary tool calls.

2. Support both execution modes.
- If terminal execution is available, run probes and report observed output.
- If execution is unavailable, provide exact commands and expected results for manual run.

3. Return a consistent output package.
- Include a complete `.stoverride` YAML block with `name` and `desc`.
- Include install steps via Stash UI and URL import path when relevant.
- Include verification commands and pass/fail interpretation.

## Templates

### Base override skeleton

```yaml
name: |-
  <Override Name>
desc: |-
  <What this override changes>
```

### Docker fake-IP bypass override

```yaml
name: |-
  Docker FakeIP Bypass
desc: |-
  Bypass fake-ip for Docker registry domains
dns:
  fake-ip-filter:
    - +.docker.io
    - registry-1.docker.io
    - auth.docker.io
    - index.docker.io
    - production.cloudflare.docker.com
```

## Validation Commands

Use these after enabling an override that touches Docker access:

```bash
dig +short registry-1.docker.io
dig +short auth.docker.io
docker pull --quiet hello-world
```

Expected:
- DNS does not return fake-IP addresses in `198.18.0.0/15`.
- Docker pull succeeds.

## Troubleshooting

- Override appears installed but has no effect:
  - Confirm Overrides toggle is ON globally.
  - Confirm the specific override toggle is ON.
  - Confirm a base config is selected in Configs.
  - Reload/restart Stash core and retest.

- User selected `.stoverride` as active config:
  - Switch active config back to base profile.
  - Keep `.stoverride` only in Overrides.

- Update fails in Overrides list:
  - Treat as remote refresh issue.
  - Verify current runtime behavior with DNS and connectivity probes before changing anything else.
