# Digital Twin Universe — Validation Profiles

This folder ships reusable [Digital Twin Universe](https://github.com/microsoft/amplifier-bundle-digital-twin-universe)
(DTU) profiles for validating `amplifier-bundle-perplexity` in an isolated
Incus container, exactly as an end user would install it.

## Profiles

| Profile | Validates |
|---------|-----------|
| `profiles/perplexity-bundle-validation.yaml` | Both documented install paths: (1) **behavior-layer** install (`--app`, layers the thin `behaviors/perplexity-research.yaml` onto an existing foundation app without double-loading foundation); (2) **standalone** root-bundle install (`bundle add` + `bundle use perplexity`, pulls foundation + behavior). Confirms the `tool-perplexity-search` tool and `perplexity:research-expert` agent load in both. |

## Prerequisites

- `amplifier-digital-twin` CLI — `uv tool install git+https://github.com/microsoft/amplifier-bundle-digital-twin-universe@main`
- `incus` (container runtime) and `docker` (for Gitea)
- `amplifier-gitea` CLI — `uv tool install git+https://github.com/microsoft/amplifier-bundle-gitea@main`

## Re-running the validation against your LOCAL working tree

This tests uncommitted changes without pushing to GitHub. The profile's
`url_rewrites` redirect the bundle's own `github.com/colombod/...`
self-references to a local Gitea copy, so the container installs *your* code.

```bash
# 1. Start or reuse a Gitea instance
amplifier-gitea list                 # reuse a running one, or:
amplifier-gitea create --port 10110
amplifier-gitea token <gitea-id>     # -> GITEA_TOKEN

# 2. Mirror the repo, then snapshot-push your working tree (captures
#    staged + unstaged + untracked + deletions) to admin/amplifier-bundle-perplexity
amplifier-gitea mirror-from-github <gitea-id> \
  --github-repo https://github.com/colombod/amplifier-bundle-perplexity
#    (snapshot-push: clone --local into a temp dir, overlay working-tree files,
#     commit once, push --force to the Gitea 'main' branch. NEVER commit in the
#     source repo.)

# 3. Find a host IP the container can reach (Incus bridge gateway is reliable)
incus network get incusbr0 ipv4.address     # e.g. 10.160.61.1/24

# 4. Launch
amplifier-digital-twin launch \
  .amplifier/digital-twin-universe/profiles/perplexity-bundle-validation.yaml \
  --var GITEA_URL=http://<host-ip>:<port> \
  --var GITEA_TOKEN=<token> \
  --name perplexity-validation

# 5. Wait for readiness, then inspect
amplifier-digital-twin check-readiness perplexity-validation     # {"ready": true}

# Confirm the secret reached the container (masked) -- the tool needs this
amplifier-digital-twin exec perplexity-validation -- \
  bash -c 'echo "PERPLEXITY_API_KEY ${PERPLEXITY_API_KEY:+SET prefix=${PERPLEXITY_API_KEY:0:5}}"'
#   -> PERPLEXITY_API_KEY SET prefix=pplx-

# Behavior-layer (Goal 1): thin behavior, NO foundation duplication
amplifier-digital-twin exec perplexity-validation -- \
  amplifier bundle show perplexity-research-behavior
#   -> tools: (1) tool-perplexity-search ; agents: (1) perplexity:research-expert ; providers: none

# Standalone (Goal 2): foundation + behavior
amplifier-digital-twin exec perplexity-validation -- amplifier bundle current
amplifier-digital-twin exec perplexity-validation -- amplifier bundle show perplexity
#   -> tool-perplexity-search among 14 tools ; perplexity:research-expert among 40 agents

# 6. REAL end-to-end test -- live Perplexity API call through the tool.
#    Requires PERPLEXITY_API_KEY forwarded (step 0/secret section below).
amplifier-digital-twin exec perplexity-validation -- \
  bash -c 'cd /home/user/project && amplifier run "Use the perplexity_research tool to research: What are the latest developments in fusion energy in 2025? Return the tool output verbatim including the References section with URLs and the Tokens line."'
#   -> real research content + categorized References (Academic/News/Other) with
#      URLs + a "Tokens: <n>" line. If you instead see
#      "PERPLEXITY_API_KEY not set", the secret was NOT forwarded -- see below.

# 7. Re-test after more local edits: re-push to Gitea, then
amplifier-digital-twin update perplexity-validation

# 8. Tear down
amplifier-digital-twin destroy perplexity-validation
```

## Validating the PUBLISHED GitHub state instead

Delete the `url_rewrites:` section from the profile (and drop the `GITEA_*`
`--var` flags). The `github.com/colombod/...` URLs then resolve straight from
GitHub — useful as a post-merge smoke test.

## Notes

- `PERPLEXITY_API_KEY` is only needed for *live* research calls. Structural
  validation (bundle resolution, tool registration, agent availability) does
  not require it. The profile forwards it via `passthrough` if present.
- `ANTHROPIC_API_KEY` is forwarded so `amplifier run` has a working provider.
- Launch provisioning takes a few minutes (installs Amplifier + foundation +
  the bundle). Run it in the background and poll `check-readiness`.
