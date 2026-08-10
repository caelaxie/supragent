#!/usr/bin/env bash
# Validate that this repository is a valid npx skills package source.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v npx >/dev/null 2>&1; then
  echo "error: npx is required (Node.js)" >&2
  exit 1
fi

mapfile -t expected < <(
  find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print \
    | sed 's|^skills/||; s|/SKILL.md$||' \
    | sort
)

if [[ ${#expected[@]} -eq 0 ]]; then
  echo "error: no skills/*/SKILL.md files found" >&2
  exit 1
fi

echo "Expected ${#expected[@]} skill(s) from filesystem:"
printf '  - %s\n' "${expected[@]}"

# Agent Skills name constraints (agentskills.io + skills CLI)
NAME_RE='^[a-z0-9]+(-[a-z0-9]+)*$'
for skill in "${expected[@]}"; do
  skill_md="skills/${skill}/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    echo "error: missing $skill_md" >&2
    exit 1
  fi

  if [[ ! "$skill" =~ $NAME_RE ]]; then
    echo "error: folder name '$skill' is not a valid skill name (a-z0-9 and single hyphens)" >&2
    exit 1
  fi
  if (( ${#skill} > 64 )); then
    echo "error: skill name '$skill' exceeds 64 characters" >&2
    exit 1
  fi

  # Extract frontmatter name/description without requiring yq
  name="$(
    awk '
      BEGIN { in_fm=0 }
      /^---[[:space:]]*$/ {
        if (in_fm == 0) { in_fm=1; next }
        else exit
      }
      in_fm && /^name:[[:space:]]*/ {
        sub(/^name:[[:space:]]*/, "")
        print
        exit
      }
    ' "$skill_md"
  )"
  description="$(
    awk '
      BEGIN { in_fm=0 }
      /^---[[:space:]]*$/ {
        if (in_fm == 0) { in_fm=1; next }
        else exit
      }
      in_fm && /^description:[[:space:]]*/ {
        sub(/^description:[[:space:]]*/, "")
        print
        exit
      }
    ' "$skill_md"
  )"

  if [[ -z "$name" ]]; then
    echo "error: $skill_md missing required frontmatter field: name" >&2
    exit 1
  fi
  if [[ -z "$description" ]]; then
    echo "error: $skill_md missing required frontmatter field: description" >&2
    exit 1
  fi
  if [[ "$name" != "$skill" ]]; then
    echo "error: $skill_md name '$name' must match folder name '$skill'" >&2
    exit 1
  fi
  if (( ${#description} > 1024 )); then
    echo "error: $skill_md description exceeds 1024 characters (${#description})" >&2
    exit 1
  fi
done

if [[ -f skills.sh.json ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import json
from pathlib import Path

catalog = json.loads(Path("skills.sh.json").read_text())
skills = sorted(
    p.parent.name
    for p in Path("skills").glob("*/SKILL.md")
)
grouped = []
for group in catalog.get("groupings", []):
    grouped.extend(group.get("skills", []))
missing = sorted(set(skills) - set(grouped))
unknown = sorted(set(grouped) - set(skills))
if unknown:
    raise SystemExit(f"skills.sh.json references unknown skills: {', '.join(unknown)}")
if missing:
    print(f"note: skills.sh.json does not group: {', '.join(missing)}")
else:
    print("skills.sh.json groups every skill")
PY
  else
    echo "note: python3 not found; skipped skills.sh.json cross-check"
  fi
fi

echo
echo "Discovering skills via npx skills..."
list_output="$(npx --yes skills add . --list 2>&1)"
printf '%s\n' "$list_output"

# Parse discovered skill names from CLI list output.
# List mode prints each skill name on its own line (often with box-drawing prefixes
# and, under CI, ANSI color codes), followed by a longer description line.
# Strip CSI/OSC escapes first so slug matching is stable in GitHub Actions.
strip_ansi() {
  # CSI sequences (e.g. \x1b[36m, \x1b[0m, \x1b[?25h) and OSC sequences.
  sed -E $'s/\x1B\\[[0-9;?]*[A-Za-z]//g; s/\x1B\\][^\x07]*(\x07|\x1B\\\\)//g'
}

found_count="$(
  printf '%s\n' "$list_output" \
    | strip_ansi \
    | sed -nE 's/.*Found ([0-9]+) skills.*/\1/p' \
    | head -1
)"

mapfile -t discovered < <(
  printf '%s\n' "$list_output" \
    | strip_ansi \
    | while IFS= read -r line; do
        # Drop leading decoration (box-drawing, spaces, symbols), keep pure skill slugs.
        cleaned="$(
          printf '%s\n' "$line" \
            | sed -E 's/^[^a-z0-9]+//; s/[[:space:]]+$//'
        )"
        if [[ "$cleaned" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
          printf '%s\n' "$cleaned"
        fi
      done \
    | sort -u
)

# Keep only names that correspond to expected skills (ignore noise like "skills").
filtered=()
for d in "${discovered[@]+"${discovered[@]}"}"; do
  for skill in "${expected[@]}"; do
    if [[ "$d" == "$skill" ]]; then
      filtered+=("$d")
      break
    fi
  done
done
discovered=("${filtered[@]+"${filtered[@]}"}")

if [[ -n "$found_count" && "$found_count" != "${#expected[@]}" ]]; then
  echo "error: npx skills reported Found ${found_count} skills, expected ${#expected[@]}" >&2
  exit 1
fi

if [[ ${#discovered[@]} -eq 0 ]]; then
  echo "error: npx skills discovered 0 skills" >&2
  exit 1
fi

echo
echo "Discovered ${#discovered[@]} skill(s) via npx skills:"
printf '  - %s\n' "${discovered[@]}"

missing=()
for skill in "${expected[@]}"; do
  found=0
  for d in "${discovered[@]}"; do
    if [[ "$d" == "$skill" ]]; then
      found=1
      break
    fi
  done
  if [[ $found -eq 0 ]]; then
    missing+=("$skill")
  fi
done

extra=()
for d in "${discovered[@]}"; do
  found=0
  for skill in "${expected[@]}"; do
    if [[ "$skill" == "$d" ]]; then
      found=1
      break
    fi
  done
  if [[ $found -eq 0 ]]; then
    extra+=("$d")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "error: skills present on disk but not discovered by npx skills:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  exit 1
fi

if [[ ${#extra[@]} -gt 0 ]]; then
  echo "error: skills discovered by npx skills but missing on disk under skills/:" >&2
  printf '  - %s\n' "${extra[@]}" >&2
  exit 1
fi

echo
echo "OK: all ${#expected[@]} skills are discoverable by npx skills"
