---
name: stash-override-rules
description: Create, adjust, and validate Stash VPN overrides (`.stoverride`) and installable script packages (`.js` + wrapper override) for DNS, fake-IP filtering, rules, routing behavior, HTTP rewrite scripts, cron scripts, and one-click import links. Use when asked to build or troubleshoot Stash overrides, package a script so Stash can install it, use Script Hub patterns, install by URL, merge override patches into an active profile, or verify that override changes are taking effect at runtime.
---

# Stash Override Rules

## Goal

Produce the smallest Stash artifact that solves the user's networking goal:

- A minimal `.stoverride` patch for declarative config changes.
- A Stash-installable script package for runtime logic, following the Script Hub pattern from `http://script.hub` / `https://script.hub`: raw `.js` hosted remotely plus a wrapper `.stoverride` that wires the script through `script-providers`.

## Workflow

1. Identify the exact intent and success signal.
- Infer the expected behavior from context when clear.
- Ask a clarifying question only when success criteria are ambiguous.
- Define an observable check such as DNS resolution, `curl`, Stash import success, or app behavior.

2. Choose artifact mode before writing anything.
- Use `.stoverride` only for declarative changes such as `dns`, fake-IP filters, `rules`, `rule-providers`, `hosts`, routing, or other config patch keys.
- Use a script package when the user asks for a script, automation, request/response rewriting logic, scheduled execution, a panel/tile-style script integration, or anything "installable by Stash".
- If the request mentions Script Hub or asks for an installable Stash script, default to `.js` plus wrapper `.stoverride`, not bare JS.

3. Build only the required keys and code.
- Keep override patches short and explicit.
- Avoid copying a whole base profile into override content.
- For script mode, keep the JavaScript self-contained and compatible with Stash runtime globals.
- Stash does not require `#!name=` style headers inside the `.js` file. Metadata lives in the wrapper override.

4. Package scripts the way Stash actually installs them.
- Do not present bare `.js` as the final install artifact.
- Return a hostable raw `.js` URL and a companion `.stoverride` wrapper.
- Use `script-providers` for remote JS distribution.
- Use `payload` or `path` only for local/debug flows when remote hosting is unavailable.
- Bind the provider under the correct Stash section such as `http.script`, `cron.script`, or another documented script consumer.
- Follow the Script Hub module shape: top-level metadata, only the required Stash section, then `script-providers`.
- When uncertain, mirror the layout used by Script Hub's own Stash module at `https://raw.githubusercontent.com/Script-Hub-Org/Script-Hub/main/modules/script-hub.stash.stoverride`.

5. Ensure override metadata and install path are present.
- Always include `name` and `desc` in generated override YAML.
- Use a descriptive, task-specific name.
- For shared or published installable wrappers, add `author`, `icon`, and `category` when those values are known and useful.
- When the artifact is meant for one-click install, return one of these forms:
- `stash://install-override?url=<url-encoded-wrapper-url>`
- `https://link.stash.ws/install-override/<domain>/<path-to-override>`

6. Verify the runtime effect.
- Confirm the raw `.js` URL returns JavaScript.
- Confirm the wrapper URL returns valid YAML.
- Validate the install link format when one is included.
- Run probes that match the user's request, not generic checks.

## Cross-Agent Compatibility

Use this contract so the skill works across different coding agents and toolchains:

1. Use agent-neutral artifacts.
- Emit YAML, JavaScript, install URLs, and shell commands only.
- Avoid agent-specific APIs, memory features, or proprietary tool calls.

2. Support both execution modes.
- If terminal execution is available, run probes and report observed output.
- If execution is unavailable, provide exact commands and expected results for manual run.

3. Return a consistent output package.
- For override-only requests: return a complete `.stoverride` YAML block with `name` and `desc`.
- For script-package requests: return the `.js` source, the wrapper `.stoverride`, the expected hosting paths or raw URLs, and an install link when relevant.
- Always include verification commands and pass/fail interpretation.

## Templates

### Base override skeleton

```yaml
name: |-
  <Override Name>
desc: |-
  <What this override changes>
```

### Installable HTTP script wrapper

```yaml
name: |-
  <Override Name>
desc: |-
  Install <Script Name> into Stash via script-providers
author: <Optional Author>
icon: <Optional Icon URL>
category: <Optional Category>
http:
  # Add force-http-engine or mitm when the target flow requires interception.
  script:
    - match: <url-regex>
      name: <Script Name>
      type: request # or response
      require-body: false
      timeout: 20
script-providers:
  <Script Name>:
    url: https://example.com/<script-name>.js
    interval: 86400
```

### Installable cron script wrapper

```yaml
name: |-
  <Override Name>
desc: |-
  Install <Script Name> as a Stash cron script
author: <Optional Author>
icon: <Optional Icon URL>
category: <Optional Category>
cron:
  script:
    - name: <Script Name>
      cron: "0 * * * *"
      timeout: 20
script-providers:
  <Script Name>:
    url: https://example.com/<script-name>.js
    interval: 86400
```

### Minimal Stash script skeleton

```javascript
const url = typeof $request !== "undefined" ? $request.url : "";

// Add only the logic needed for the user's rule or rewrite.

$done({});
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

Use these for installable script packages:

```bash
curl -L <raw-js-url> | sed -n '1,80p'
curl -L <wrapper-override-url> | sed -n '1,120p'
```

Use these after enabling an override that touches Docker access:

```bash
dig +short registry-1.docker.io
dig +short auth.docker.io
docker pull --quiet hello-world
```

Expected:
- DNS does not return fake-IP addresses in `198.18.0.0/15`.
- Raw script response is JavaScript, not HTML.
- Wrapper response includes the expected `name`, `desc`, and `script-providers` wiring.
- Docker pull succeeds when the request is Docker-related.

## Troubleshooting

- Script imports but does not run:
  - Confirm the wrapper binds the script under the correct Stash section.
  - Confirm the match pattern or cron expression actually triggers.
  - Confirm the script ends with `$done(...)`.

- Bare `.js` was shared as the install artifact:
  - Wrap it in a `.stoverride` using `script-providers`.
  - Stash installs the override, then fetches the remote JS from the provider URL.

- Override appears installed but has no effect:
  - Confirm Overrides toggle is ON globally.
  - Confirm the specific override toggle is ON.
  - Confirm a base config is selected in Configs.
  - Reload or restart Stash core and retest.

- HTTP script does not trigger:
  - Confirm `http.force-http-engine` or `http.mitm` are present when the flow requires them.
  - Confirm the request actually matches the configured regex.

- Remote update does not appear in Stash:
  - Treat it as a script-provider cache issue first.
  - Check the provider `interval`.
  - If needed for debugging, seed with `payload` and keep the final artifact remote.

- User selected `.stoverride` as the active config:
  - Switch the active config back to the base profile.
  - Keep `.stoverride` only in Overrides.
