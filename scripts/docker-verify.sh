#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  printf 'docker: command not found\n' >&2
  exit 127
fi

printf '%s\n' '==> Docker Compose configuration'
COMPOSE=(docker compose)
cleanup() {
  "${COMPOSE[@]}" down
}
trap cleanup EXIT

"${COMPOSE[@]}" config
printf '%s\n' '==> Docker image build'
"${COMPOSE[@]}" build
printf '%s\n' '==> Docker service start'
"${COMPOSE[@]}" up -d
printf '%s\n' '==> Waiting for Docker service readiness'
ready=0
for ((attempt = 1; attempt <= 30; attempt++)); do
  status=$("${COMPOSE[@]}" ps --format '{{.State}} {{.Health}}' almond 2>/dev/null || true)
  case "$status" in
    *'running healthy'*)
      ready=1
      break
      ;;
    *'exited'*|*'dead'*|*'unhealthy'*)
      printf 'Docker service failed to become ready: %s\n' "$status" >&2
      "${COMPOSE[@]}" ps >&2
      exit 1
      ;;
  esac
  sleep 1
done
if (( ! ready )); then
  printf '%s\n' 'Docker service did not become ready within 30 seconds' >&2
  "${COMPOSE[@]}" ps >&2
  exit 1
fi
printf '%s\n' '==> Docker health check'
"${COMPOSE[@]}" exec -T almond python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"
printf '%s\n' '==> Docker service shutdown'
"${COMPOSE[@]}" down
trap - EXIT
printf '%s\n' 'ALMOND DOCKER VERIFY: PASS'
