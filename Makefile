.PHONY: build run

build:
	docker build -t metro-parser .

run:
	docker run --env-file ./.env-non-dev -v $(shell pwd):/app metro-parser
