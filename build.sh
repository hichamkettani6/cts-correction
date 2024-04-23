#!/bin/bash
docker build --rm -f Dockerfile --build-arg TZ="Europe/Rome" --network host -t inrim_cts_correction:latest .

docker compose -f docker-compose-mock.yml stop
docker compose -f docker-compose-mock.yml build --no-cache .
docker compose -f docker-compose-mock.yml up

