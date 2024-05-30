#!/bin/bash

source .env

docker compose down
#docker compose -f docker-compose-mock.yml build --no-cache .
docker compose up -d