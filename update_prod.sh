#!/bin/bash

source .env

docker compose -f docker-compose-prod.yml down
#docker compose -f docker-compose-mock.yml build --no-cache .
docker compose -f docker-compose-prod.yml up -d