#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

stage() {
  local name="$1"
  shift
  printf '\n==> %s\n' "$name"
  "$@"
}

artifact_check() {
  local path
  for path in \
    Makefile README.md \
    scripts/verify.sh scripts/docker-verify.sh \
    package.json package-lock.json playwright.config.mjs e2e/dashboard.spec.mjs \
    src/almond/api.py \
    web/index.html web/app.js web/styles.css \
    Dockerfile docker-compose.yml .dockerignore \
    tests/test_api.py tests/test_cli.py tests/test_engine.py tests/test_docker_config.py \
    docs/ALMOND_TECHNICAL_REPORT.tex docs/ARCHITECTURE.md docs/ASSUMPTIONS.md \
    docs/AI_ENGINEERING_LOG.md docs/DEMO_SCRIPT.md docs/RELEASE_CHECKLIST.md \
    constraints.yaml; do
    [[ -f "$path" ]] || { printf 'Missing required artifact: %s\n' "$path" >&2; return 1; }
  done
}

stage "Python unit and API tests" .venv/bin/pytest -q
stage "Browser end-to-end tests" npm run test:e2e
stage "JavaScript syntax" node --check web/app.js

stage "Deterministic CLI output" bash -c '
  first=$(mktemp)
  second=$(mktemp)
  trap "rm -f \"$first\" \"$second\"" EXIT
  .venv/bin/almond >"$first"
  .venv/bin/almond >"$second"
  cmp -s "$first" "$second"
'

stage "Two-pass technical report compilation" bash -c '
  output_dir=$(mktemp -d)
  trap "rm -rf \"$output_dir\"" EXIT
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$output_dir" docs/ALMOND_TECHNICAL_REPORT.tex
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$output_dir" docs/ALMOND_TECHNICAL_REPORT.tex
  [[ -s "$output_dir/ALMOND_TECHNICAL_REPORT.pdf" ]]
'

stage "Required release artifacts" artifact_check
printf '\nALMOND VERIFY: PASS\n'
