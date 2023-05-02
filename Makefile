SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:

MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

COMMA := ,

install: poetry install
.PHONY: install

venv: poetry shell
.PHONY: venv

lint-fix: ## Fix lint
	isort .
	black .
.PHONY: lint-fix

clean:  ## Clean cache files
	find . -name '__pycache__' -type d | xargs rm -rvf
	find . -name '.mypy_cache' -type d | xargs rm -rvf
	find . -name '.pytest_cache' -type d | xargs rm -rvf
.PHONY: clean

build: Dockerfile  ## Build docker image
	docker build \
		-f $^ \
		--tag imgur-minio:latest .
.PHONY: build

up:
	DOCKER_DEFAULT_PLATFORM=linux/amd64 docker run -d \
	-p 8000:8000 \
	--env-file .env \
	-v ./apikeys.json:/code/apikeys.json \
	--name imgur-minio \
	imgur-minio:latest
.PHONY: up

run:  ## Run dev server
	uvicorn main:app --reload
.PHONY: run

.DEFAULT_GOAL := help
help: Makefile
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'
.PHONY: help
