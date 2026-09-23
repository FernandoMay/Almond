.PHONY: verify docker-verify docker-up docker-health docker-down docker-validate

verify:
	./scripts/verify.sh

docker-verify:
	./scripts/docker-verify.sh

docker-up:
	docker compose up --build -d

docker-health:
	docker compose exec -T almond python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"

docker-down:
	docker compose down

docker-validate:
	docker compose config
