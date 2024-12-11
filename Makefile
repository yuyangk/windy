.ONESHELL:
.PHONY: run build shell

SHELL := bash

export MY_UID = $(shell id -u)
export MY_GID = $(shell id -g)

windy-gfs: 
	docker compose run --rm windy-gfs

windy-ec: 
	docker compose run --rm windy-ec

shell:
	docker run \
	-it --rm \
	--volume `pwd`:/app \
	windy:$(VERSION) \
	bash
