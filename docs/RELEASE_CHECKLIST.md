# Release checklist

## Verified by `make verify`

- [x] `.venv/bin/pytest -q`
- [x] `npm run test:e2e`
- [x] `node --check web/app.js`
- [x] Two no-argument `.venv/bin/almond` outputs are byte-identical.
- [x] The technical report compiles twice with `pdflatex` and produces a non-empty PDF.
- [x] Required API, web, Docker, test, constraint, demo, and report artifacts exist.

## Separate Docker boundary

- [ ] `docker compose config`, image build, service start, `/health` check, and shutdown are pending until Docker is installed and available.
- [x] The exact unavailable-environment result is `docker: command not found`.
- [ ] Do not interpret `make verify` as Docker verification. Run `make docker-verify` separately.

## Explicitly not release claims

Persistence, authentication, cloud deployment, asynchronous job storage, payroll/legal approval, and production hardening remain planned. The `39.14%` result is scenario-specific and must not be presented as universal savings.
